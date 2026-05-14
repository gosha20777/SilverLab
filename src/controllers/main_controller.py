import os
import cv2
from PySide6.QtCore import QObject, Signal, Slot, QThreadPool
from src.models.frame_container import FrameContainer
from src.models.image_sequence import ImageSequence
from src.core.isp.pipeline import ISPPipeline
from src.core.io.reader import read_image, generate_thumbnail
from src.core.io.writer import save_image
from src.utils.concurrency import Worker


class MainController(QObject):
    """
    Main orchestrator for the SilverLab application.
    Handles communication between the UI, the Models, and the ISP Core.
    """
    # Signals to communicate with the UI
    image_loaded = Signal(object)  # Emits the updated FrameContainer
    image_processed = Signal(object)
    thumbnail_ready = Signal(str, object) # Emits (file_path, thumbnail_ndarray)
    folder_loaded = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.sequence = ImageSequence()
        self.isp_pipeline = ISPPipeline()
        self.thread_pool = QThreadPool.globalInstance()
        self._active_workers = set()

    def load_image(self, file_path: str) -> None:
        """
        Loads an image from disk using OpenCV (IMREAD_UNCHANGED) and initializes the container.
        """
        image_data = read_image(file_path)
        if image_data is None:
            print(f"Failed to load image at {file_path}")
            return

        container = FrameContainer(file_path, image_data)
        
        # Find index
        idx = self.sequence.file_paths.index(file_path) if file_path in self.sequence.file_paths else -1
        self.sequence.set_active(idx, container)
        
        # Run initial ISP to populate the cache
        self.isp_pipeline.process_container(self.sequence.active_container)
        
        self.image_loaded.emit(self.sequence.active_container)

    def load_files(self, file_paths: list[str]) -> None:
        """
        Clears current sequence, sets new files, and generates thumbnails.
        Automatically loads the first image to the canvas.
        """
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
        """
        Scans folder for images, resets sequence, and fires thumbnail workers.
        """
        valid_exts = ('.tiff', '.tif', '.jpg', '.jpeg', '.png')
        files = []
        for f in os.listdir(folder_path):
            if f.lower().endswith(valid_exts):
                files.append(os.path.join(folder_path, f))
                
        files.sort()
        self.load_files(files)

    def _on_thumbnail_result_tuple(self, result: tuple) -> None:
        file_path, thumbnail_data = result
        if thumbnail_data is not None:
            self.thumbnail_ready.emit(file_path, thumbnail_data)

    def save_current_image(self, save_path: str) -> bool:
        """
        Saves the current cached display image to the given path.
        """
        if not self.sequence.active_container:
            return False
            
        display_img = self.sequence.active_container.get_display_image()
        return save_image(display_img, save_path)

    @Slot(float)
    def on_exposure_value_changed(self, value: float) -> None:
        """
        Slot connected to the UI's exposure slider.
        Updates the model and requests ISP processing.
        """
        if self.sequence.active_container is None:
            return

        self.sequence.active_container.exposure_value = value
        
        # In MVP we run this synchronously. In future, use QThreadPool here.
        self.isp_pipeline.process_container(self.sequence.active_container)
        
        self.image_processed.emit(self.sequence.active_container)
