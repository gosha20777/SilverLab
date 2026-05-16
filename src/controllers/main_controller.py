import os
import cv2
from PySide6.QtCore import QObject, Signal, Slot, QThreadPool
from src.models.frame_container import FrameContainer
from src.models.image_sequence import ImageSequence
from src.core.isp.pipeline import ISPPipeline
from src.core.io.reader import read_image, generate_thumbnail
from src.core.io.writer import save_image
from src.utils.concurrency import Worker


from src.models.isp_config import PipelineConfig

class MainController(QObject):
    """
    Main orchestrator for the SilverLab application.
    Handles communication between the UI, the Models, and the ISP Core.
    """
    # Signals to communicate with the UI
    image_loaded = Signal(object)  # Emits the updated FrameContainer
    image_processed = Signal(object)
    proxy_processed = Signal(object)
    thumbnail_ready = Signal(str, object)
    folder_loaded = Signal()
    status_message_changed = Signal(str)
    pipeline_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.sequence = ImageSequence()
        self.isp_pipeline = ISPPipeline()
        self.thread_pool = QThreadPool.globalInstance()
        self._active_workers = set()
        self.current_job_id = 0
        self.current_preset = self._load_default_preset()

    def _load_default_preset(self) -> PipelineConfig:
        try:
            return PipelineConfig.from_yaml("presets/default.yaml")
        except Exception as e:
            print(f"Could not load default preset, using empty: {e}")
            return PipelineConfig()

    def _trigger_pipeline(self, start_node_index: int = 0, is_interactive: bool = False) -> None:
        """
        Triggers ISP processing. If interactive, processes proxy synchronously.
        If not interactive, triggers proxy synchronously, then dispatches background job for full res.
        """
        if not self.sequence.active_container:
            return
            
        container = self.sequence.active_container
        
        # 1. Fast Proxy Process (Synchronous)
        self.isp_pipeline.process_container(container, is_proxy=True, start_node_index=start_node_index)
        self.proxy_processed.emit(container)
        
        if is_interactive:
            return
            
        # 2. Full Process (Asynchronous)
        self.current_job_id += 1
        job_id = self.current_job_id
        
        def task():
            self.isp_pipeline.process_container(container, is_proxy=False, start_node_index=0)
            return container

        worker = Worker(task)
        self._active_workers.add(worker)
        
        def on_result(res_container):
            if self.current_job_id == job_id:
                self.image_processed.emit(res_container)
                
        worker.signals.result.connect(on_result)
        worker.signals.finished.connect(lambda w=worker: self._active_workers.discard(w))
        self.thread_pool.start(worker)

    def load_image(self, file_path: str) -> None:
        image_data = read_image(file_path)
        if image_data is None: return

        # Find SequenceItem
        item = next((it for it in self.sequence.items if it.file_path == file_path), None)
        idx = self.sequence.items.index(item) if item else -1
        
        # Assign config
        if item is not None:
            if item.pipeline_config is None:
                item.pipeline_config = self.current_preset.model_copy(deep=True)
        else:
            print("Warning: Loaded image not in sequence items.")

        container = FrameContainer(file_path, image_data)
        if item is not None and item.pipeline_config is not None:
            container.pipeline_config = item.pipeline_config

        self.sequence.set_active(idx, container)
        
        self.image_loaded.emit(self.sequence.active_container)
        self.pipeline_changed.emit()
        self._trigger_pipeline(is_interactive=False)

    def apply_to_all(self) -> None:
        """Applies the current active config to all sequence items."""
        if not self.sequence.active_container: return
        
        current_config = self.sequence.active_container.pipeline_config
        self.current_preset = current_config.model_copy(deep=True) # Update global preset logic
        
        for item in self.sequence.items:
            new_config = current_config.model_copy(deep=True)
            for node in new_config.nodes:
                if getattr(node, "node_type", "") == "SplitterNode":
                    node.mode = "auto_diptych"
                    node.current_angle = 0.0
            item.pipeline_config = new_config
            
        self.status_message_changed.emit(f"Пресет применен ко всем {len(self.sequence.items)} файлам.")

    def load_files(self, file_paths: list[str]) -> None:
        self.sequence.set_files(file_paths)
        self.folder_loaded.emit()

        for f in file_paths:
            def make_task(path):
                return lambda: (path, generate_thumbnail(path))

            worker = Worker(make_task(f))
            self._active_workers.add(worker)
            worker.signals.result.connect(self._on_thumbnail_result_tuple)
            worker.signals.finished.connect(lambda w=worker: self._active_workers.discard(w))
            self.thread_pool.start(worker)
            
        if file_paths:
            self.load_image(file_paths[0])

    def load_folder(self, folder_path: str) -> None:
        valid_exts = ('.tiff', '.tif', '.jpg', '.jpeg', '.png')
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(valid_exts)]
        files.sort()
        self.load_files(files)

    def _on_thumbnail_result_tuple(self, result: tuple) -> None:
        file_path, thumbnail_data = result
        if thumbnail_data is not None:
            self.thumbnail_ready.emit(file_path, thumbnail_data)

    def save_current_image(self, save_path: str) -> bool:
        if not self.sequence.active_container: return False
        display_img = self.sequence.active_container.get_display_image(is_proxy=False)
        
        # Apply final crop if necessary
        config = self.sequence.active_container.pipeline_config
        for node in config.nodes:
            if getattr(node, "node_type", "") == "SplitterNode" and getattr(node, "enabled", True):
                fx, fy, fw, fh = getattr(node, 'final_crop', (0.0, 0.0, 1.0, 1.0))
                bg_h, bg_w = display_img.shape[:2]
                l, t = max(0, int(round(fx * bg_w))), max(0, int(round(fy * bg_h)))
                r, b = min(bg_w, int(round((fx + fw) * bg_w))), min(bg_h, int(round((fy + fh) * bg_h)))
                if l < r and t < b:
                    display_img = display_img[t:b, l:r]
                break
            elif getattr(node, "node_type", "") == "CropNode" and getattr(node, "enabled", True):
                nx, ny, nw, nh = getattr(node, 'bbox', (0.0, 0.0, 1.0, 1.0))
                bg_h, bg_w = display_img.shape[:2]
                l, t = max(0, int(round(nx * bg_w))), max(0, int(round(ny * bg_h)))
                r, b = min(bg_w, int(round((nx + nw) * bg_w))), min(bg_h, int(round((ny + nh) * bg_h)))
                if l < r and t < b:
                    display_img = display_img[t:b, l:r]
                break
                
        return save_image(display_img, save_path)

    def update_node_config_interactive(self, index: int, **kwargs) -> None:
        if not self.sequence.active_container: return
        config = self.sequence.active_container.pipeline_config
        if 0 <= index < len(config.nodes):
            for k, v in kwargs.items():
                if hasattr(config.nodes[index], k):
                    setattr(config.nodes[index], k, v)
            self._trigger_pipeline(start_node_index=index, is_interactive=True)

    def update_node_config_final(self) -> None:
        # Full recalculation after slider release
        self._trigger_pipeline(start_node_index=0, is_interactive=False)

    def add_node(self, node_config) -> None:
        if not self.sequence.active_container: return
        self.sequence.active_container.pipeline_config.nodes.append(node_config)
        self.pipeline_changed.emit()
        self._trigger_pipeline(is_interactive=False)

    def delete_node(self, index: int) -> None:
        if not self.sequence.active_container: return
        config = self.sequence.active_container.pipeline_config
        if 0 <= index < len(config.nodes):
            config.nodes.pop(index)
            self.pipeline_changed.emit()
            # Start from the index where deletion happened (for proxy)
            self._trigger_pipeline(start_node_index=max(0, index), is_interactive=False)

    def move_node(self, index: int, direction: int) -> None:
        if not self.sequence.active_container: return
        config = self.sequence.active_container.pipeline_config
        nodes = config.nodes
        new_index = index + direction
        if 0 <= index < len(nodes) and 0 <= new_index < len(nodes):
            nodes[index], nodes[new_index] = nodes[new_index], nodes[index]
            self.pipeline_changed.emit()
            # Cache invalidates from the top-most affected node
            self._trigger_pipeline(start_node_index=min(index, new_index), is_interactive=False)

    def toggle_node(self, index: int, state: bool) -> None:
        if not self.sequence.active_container: return
        config = self.sequence.active_container.pipeline_config
        if 0 <= index < len(config.nodes):
            config.nodes[index].enabled = state
            self._trigger_pipeline(start_node_index=index, is_interactive=False)
