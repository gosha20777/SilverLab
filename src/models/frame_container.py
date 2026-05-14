from typing import Optional
import numpy as np
from src.models.isp_config import PipelineConfig

class FrameContainer:
    """
    Pure data structure representing a single image frame.
    
    Holds the original raw 16-bit/8-bit array and its processed, 
    cached version ready for display.
    """
    def __init__(self, file_path: str, image_data: np.ndarray) -> None:
        """
        Initializes the FrameContainer.

        Args:
            file_path (str): The absolute path to the loaded file.
            image_data (np.ndarray): The raw image array read from disk.
        """
        self.file_path: str = file_path
        self.raw_image: np.ndarray = image_data
        self.cached_image: Optional[np.ndarray] = None
        
        # Local ISP parameters configuration
        self.pipeline_config: PipelineConfig = PipelineConfig()

    def update_cache(self, processed_data: np.ndarray) -> None:
        """
        Updates the cached image with newly processed data from the ISP pipeline.

        Args:
            processed_data (np.ndarray): The ISP-processed image array.
        """
        self.cached_image = processed_data

    def get_display_image(self) -> np.ndarray:
        """
        Returns the cached image if available, otherwise the raw original image.

        Returns:
            np.ndarray: The image array to be passed to the UI layer.
        """
        if self.cached_image is not None:
            return self.cached_image
        return self.raw_image
