import cv2
from PySide6.QtCore import QObject, Signal, Slot
from src.models.frame_container import FrameContainer
from src.core.isp.pipeline import ISPPipeline


class MainController(QObject):
    """
    Main orchestrator for the SilverLab application.
    Handles communication between the UI, the Models, and the ISP Core.
    """
    # Signals to communicate with the UI
    image_loaded = Signal(object)  # Emits the updated FrameContainer
    image_processed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.current_container: FrameContainer | None = None
        self.isp_pipeline = ISPPipeline()

    def load_image(self, file_path: str) -> None:
        """
        Loads an image from disk using OpenCV (IMREAD_UNCHANGED) and initializes the container.
        """
        # Load 16-bit or 8-bit image without altering depth
        image_data = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
        if image_data is None:
            print(f"Failed to load image at {file_path}")
            return

        self.current_container = FrameContainer(file_path, image_data)
        
        # Run initial ISP to populate the cache
        self.isp_pipeline.process_container(self.current_container)
        
        self.image_loaded.emit(self.current_container)

    @Slot(float)
    def on_exposure_value_changed(self, value: float) -> None:
        """
        Slot connected to the UI's exposure slider.
        Updates the model and requests ISP processing.
        """
        if self.current_container is None:
            return

        self.current_container.exposure_value = value
        
        # In MVP we run this synchronously. In future, use QThreadPool here.
        self.isp_pipeline.process_container(self.current_container)
        
        self.image_processed.emit(self.current_container)
