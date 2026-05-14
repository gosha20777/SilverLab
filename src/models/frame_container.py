from typing import Optional
import numpy as np
from src.models.isp_config import PipelineConfig

import cv2

class FrameContainer:
    """
    Pure data structure representing a single image frame.
    
    Holds the original raw 16-bit/8-bit array and its processed, 
    cached version ready for display. Also manages a Proxy (low-res) 
    version for real-time slider manipulation and a node-level cache.
    """
    def __init__(self, file_path: str, image_data: np.ndarray) -> None:
        """
        Initializes the FrameContainer and automatically generates a proxy.
        """
        self.file_path: str = file_path
        self.raw_image: np.ndarray = image_data
        self.cached_image: Optional[np.ndarray] = None
        
        # Proxy generation
        self.raw_proxy: np.ndarray = self._generate_proxy(image_data, 1024)
        self.cached_proxy: Optional[np.ndarray] = None
        
        # Node caching (Only for proxy to save RAM)
        # Stores the output image AFTER each node in the pipeline
        self.proxy_caches: list[np.ndarray] = []
        
        # Local ISP parameters configuration
        self.pipeline_config: PipelineConfig = PipelineConfig()

    def _generate_proxy(self, img: np.ndarray, max_dim: int) -> np.ndarray:
        h, w = img.shape[:2]
        scale = max_dim / max(h, w)
        if scale < 1.0:
            new_w, new_h = int(w * scale), int(h * scale)
            return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return img.copy()

    def update_cache(self, processed_data: np.ndarray, is_proxy: bool = False) -> None:
        """
        Updates the cached image.
        """
        if is_proxy:
            self.cached_proxy = processed_data
        else:
            self.cached_image = processed_data

    def get_display_image(self, is_proxy: bool = False) -> np.ndarray:
        """
        Returns the processed image.
        """
        if is_proxy:
            return self.cached_proxy if self.cached_proxy is not None else self.raw_proxy
            
        if self.cached_image is not None:
            return self.cached_image
        return self.raw_image
