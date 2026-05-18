import os
import cv2
from PySide6.QtCore import QObject, Signal, Slot, QThreadPool
from src.models.frame_container import FrameContainer
from src.models.image_sequence import ImageSequence
from src.core.isp.pipeline import ISPPipeline
from src.core.io.reader import read_image, generate_thumbnail
from src.core.io.writer import save_image
from src.core.io.image_provider import ImageProvider
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
    tool_activation_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.sequence = ImageSequence()
        self.image_provider = ImageProvider()
        self.isp_pipeline = ISPPipeline(image_provider=self.image_provider)
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
        
        # Assign config (first load only — subsequent loads reuse the same reference)
        if item is not None:
            if item.pipeline_config is None:
                item.pipeline_config = self.current_preset.model_copy(deep=True)
        else:
            print("Warning: Loaded image not in sequence items.")

        container = FrameContainer(file_path, image_data)
        self.image_provider.inject(file_path, container.raw_image, container.raw_proxy)
        if item is not None and item.pipeline_config is not None:
            # Share the SAME reference — all pipeline mutations are visible from both
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
                    node.layout_rects = []
                    # Keep region sub-pipelines intact, reset only geometry
                    for region in node.regions:
                        region.source_file = ""
                        region.bbox = (0.0, 0.0, 0.0, 0.0)
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

    def batch_export(self, output_folder: str, extension: str = ".jpg") -> None:
        import os
        from src.core.io.reader import read_image
        from src.core.io.writer import save_image
        from src.models.frame_container import FrameContainer
        from src.utils.concurrency import Worker
        
        def export_task():
            total = len(self.sequence.items)
            for i, item in enumerate(self.sequence.items):
                base_name = "export"
                if item.file_path:
                    base_name = os.path.splitext(os.path.basename(item.file_path))[0]
                    
                self.status_message_changed.emit(f"Экспорт {i+1}/{total}: {base_name}{extension}...")
                
                raw_image = read_image(item.file_path)
                if raw_image is None: continue
                
                container = FrameContainer(item.file_path, raw_image)
                self.image_provider.inject(item.file_path, container.raw_image, container.raw_proxy)
                container.pipeline_config = item.pipeline_config.model_copy(deep=True)
                
                self.isp_pipeline.process_container(container, is_proxy=False, start_node_index=0)
                display_img = container.get_display_image(is_proxy=False)
                
                # Cascading Crop logic
                final_l, final_t, final_r, final_b = 0.0, 0.0, 1.0, 1.0
                for node in container.pipeline_config.nodes:
                    if getattr(node, "enabled", True):
                        if getattr(node, "node_type", "") == "SplitterNode":
                            fx, fy, fw, fh = getattr(node, 'final_crop', (0.0, 0.0, 1.0, 1.0))
                            final_l = max(final_l, fx)
                            final_t = max(final_t, fy)
                            final_r = min(final_r, fx + fw)
                            final_b = min(final_b, fy + fh)
                        elif getattr(node, "node_type", "") == "CropNode":
                            nx, ny, nw, nh = getattr(node, 'bbox', (0.0, 0.0, 1.0, 1.0))
                            final_l = max(final_l, nx)
                            final_t = max(final_t, ny)
                            final_r = min(final_r, nx + nw)
                            final_b = min(final_b, ny + nh)
                            
                if final_l < final_r and final_t < final_b:
                    bg_h, bg_w = display_img.shape[:2]
                    l, t = max(0, int(round(final_l * bg_w))), max(0, int(round(final_t * bg_h)))
                    r, b = min(bg_w, int(round(final_r * bg_w))), min(bg_h, int(round(final_b * bg_h)))
                    display_img = display_img[t:b, l:r]
                    
                save_path = os.path.join(output_folder, f"{base_name}{extension}")
                save_image(display_img, save_path)
                
            self.status_message_changed.emit(f"Пакетный экспорт завершен! Сохранено {total} файлов.")

        worker = Worker(export_task)
        self._active_workers.add(worker)
        worker.signals.finished.connect(lambda w=worker: self._active_workers.discard(w))
        self.thread_pool.start(worker)

    def _on_thumbnail_result_tuple(self, result: tuple) -> None:
        file_path, thumbnail_data = result
        if thumbnail_data is not None:
            self.thumbnail_ready.emit(file_path, thumbnail_data)

    def save_current_image(self, save_path: str) -> bool:
        if not self.sequence.active_container: return False
        display_img = self.sequence.active_container.get_display_image(is_proxy=False)
        
        # Apply final crop if necessary (Cascading intersection)
        config = self.sequence.active_container.pipeline_config
        
        final_l, final_t, final_r, final_b = 0.0, 0.0, 1.0, 1.0
        
        for node in config.nodes:
            if getattr(node, "enabled", True):
                if getattr(node, "node_type", "") == "SplitterNode":
                    fx, fy, fw, fh = getattr(node, 'final_crop', (0.0, 0.0, 1.0, 1.0))
                    final_l = max(final_l, fx)
                    final_t = max(final_t, fy)
                    final_r = min(final_r, fx + fw)
                    final_b = min(final_b, fy + fh)
                elif getattr(node, "node_type", "") == "CropNode":
                    nx, ny, nw, nh = getattr(node, 'bbox', (0.0, 0.0, 1.0, 1.0))
                    final_l = max(final_l, nx)
                    final_t = max(final_t, ny)
                    final_r = min(final_r, nx + nw)
                    final_b = min(final_b, ny + nh)
                    
        if final_l < final_r and final_t < final_b:
            bg_h, bg_w = display_img.shape[:2]
            l, t = max(0, int(round(final_l * bg_w))), max(0, int(round(final_t * bg_h)))
            r, b = min(bg_w, int(round(final_r * bg_w))), min(bg_h, int(round(final_b * bg_h)))
            display_img = display_img[t:b, l:r]
                
        return save_image(display_img, save_path)

    def update_node_config_interactive(self, index: int, **kwargs) -> None:
        if not self.sequence.active_container: return
        config = self.sequence.active_container.pipeline_config
        if 0 <= index < len(config.nodes):
            for k, v in kwargs.items():
                if hasattr(config.nodes[index], k):
                    setattr(config.nodes[index], k, v)
            self._trigger_pipeline(start_node_index=index, is_interactive=True)

    def handle_node_action(self, node_config, action_id: str) -> None:
        if action_id == "rotate_cw":
            if hasattr(node_config, "angle_90"):
                node_config.angle_90 = (node_config.angle_90 - 90) % 360
        elif action_id == "rotate_ccw":
            if hasattr(node_config, "angle_90"):
                node_config.angle_90 = (node_config.angle_90 + 90) % 360
        elif action_id == "activate_ruler":
            self.tool_activation_requested.emit('straighten')
            return
        elif action_id == "activate_picker":
            self.tool_activation_requested.emit('picker')
            return
        elif action_id == "reset_wb":
            if hasattr(node_config, "scale_r"):
                node_config.scale_r = 1.0
                node_config.scale_g = 1.0
                node_config.scale_b = 1.0
            
        self._trigger_pipeline(start_node_index=0, is_interactive=False)

    def apply_white_balance(self, r: float, g: float, b: float) -> None:
        if not self.sequence.active_container: return
        config = self.sequence.active_container.pipeline_config
        
        wb_node = None
        for node in config.nodes:
            if getattr(node, "node_type", "") == "ManualWBNode":
                wb_node = node
                break
                
        if wb_node:
            target = (r + g + b) / 3.0
            if r > 0: wb_node.scale_r *= (target / r)
            if g > 0: wb_node.scale_g *= (target / g)
            if b > 0: wb_node.scale_b *= (target / b)
            
            # clamp scales to valid range (0 to 5)
            wb_node.scale_r = max(0.0, min(5.0, wb_node.scale_r))
            wb_node.scale_g = max(0.0, min(5.0, wb_node.scale_g))
            wb_node.scale_b = max(0.0, min(5.0, wb_node.scale_b))
            
            wb_node.enabled = True
            self.pipeline_changed.emit()
            self._trigger_pipeline(start_node_index=0, is_interactive=False)

    def apply_straighten_angle(self, angle: float) -> None:
        if not self.sequence.active_container: return
        config = self.sequence.active_container.pipeline_config
        
        # Find the rotation node
        rotation_node = None
        for node in config.nodes:
            if getattr(node, "node_type", "") == "RotationNode":
                rotation_node = node
                break
                
        if rotation_node:
            # Add to the existing angle and clamp between -45 and 45
            new_angle = rotation_node.angle + angle
            rotation_node.angle = max(-45.0, min(45.0, new_angle))
            rotation_node.enabled = True
            self.pipeline_changed.emit()
            self._trigger_pipeline(start_node_index=0, is_interactive=False)
            
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

    # --- Diptych Swap ---

    def swap_diptych_region(self, slot_index: int, source_file: str, source_region_index: int) -> None:
        """
        Replaces the content of slot `slot_index` in the active diptych
        with a region from `source_file`.

        Args:
            slot_index: Index of the target slot (layout_rect) on the current canvas.
            source_file: Path to the donor file.
            source_region_index: Index of the region to copy from the donor.
                                 -1 means "use entire file".
        """
        if not self.sequence.active_container:
            return

        config = self.sequence.active_container.pipeline_config

        # Find SplitterNode
        splitter_config = None
        for node in config.nodes:
            if getattr(node, "node_type", "") == "SplitterNode":
                splitter_config = node
                break

        if not splitter_config or slot_index >= len(splitter_config.regions):
            return

        from src.models.isp_config import RegionConfig, PipelineConfig

        if source_region_index == -1:
            # Use entire file
            splitter_config.regions[slot_index] = RegionConfig(
                source_file=source_file,
                bbox=(0.0, 0.0, 1.0, 1.0),
                pipeline=PipelineConfig(),
            )
        else:
            # Try to copy RegionConfig from donor's pipeline
            source_item = next(
                (it for it in self.sequence.items if it.file_path == source_file), None
            )
            donor_region = None
            if source_item and source_item.pipeline_config:
                for node in source_item.pipeline_config.nodes:
                    if getattr(node, "node_type", "") == "SplitterNode":
                        regions = getattr(node, "regions", [])
                        if source_region_index < len(regions):
                            donor_region = regions[source_region_index].model_copy(deep=True)
                        break

            if donor_region:
                # Ensure source_file points to the donor file
                donor_region.source_file = source_file
                splitter_config.regions[slot_index] = donor_region
            else:
                # Fallback: use entire file
                splitter_config.regions[slot_index] = RegionConfig(
                    source_file=source_file,
                    bbox=(0.0, 0.0, 1.0, 1.0),
                    pipeline=PipelineConfig(),
                )

        splitter_config.mode = "manual"
        self.pipeline_changed.emit()
        self._trigger_pipeline(start_node_index=0, is_interactive=False)
        self.status_message_changed.emit(
            f"Свап выполнен: слот {slot_index} ← {source_file.split('/')[-1]}"
        )

    def get_diptych_slot_at_point(self, norm_x: float, norm_y: float) -> int:
        """
        Determines which layout_rect slot contains the given normalized point.

        Args:
            norm_x: Normalized X coordinate (0..1).
            norm_y: Normalized Y coordinate (0..1).

        Returns:
            int: Slot index, or -1 if no slot found.
        """
        if not self.sequence.active_container:
            return -1

        for node in self.sequence.active_container.pipeline_config.nodes:
            if getattr(node, "node_type", "") == "SplitterNode":
                for i, rect in enumerate(getattr(node, "layout_rects", [])):
                    rx, ry, rw, rh = rect
                    if rx <= norm_x <= rx + rw and ry <= norm_y <= ry + rh:
                        return i
        return -1
