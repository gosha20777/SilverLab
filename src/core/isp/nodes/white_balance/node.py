import numpy as np
import cv2
from src.core.isp.nodes.base_node import BaseISPNode
from .config import ManualWBConfig

class ManualWBNode(BaseISPNode):
    """
    ISP Node for manual white balance using RGB scaling.
    """
    def process(self, image: np.ndarray, config: ManualWBConfig, **kwargs) -> np.ndarray:
        if not isinstance(config, ManualWBConfig):
            raise ValueError("Expected ManualWBConfig")
            
        if config.scale_r == 1.0 and config.scale_g == 1.0 and config.scale_b == 1.0:
            return image.copy()
            
        img_wb = image.copy()
        
        # Multiply each channel and clip to valid range
        img_wb[:, :, 0] = np.clip(img_wb[:, :, 0] * config.scale_b, 0.0, 1.0)
        img_wb[:, :, 1] = np.clip(img_wb[:, :, 1] * config.scale_g, 0.0, 1.0)
        img_wb[:, :, 2] = np.clip(img_wb[:, :, 2] * config.scale_r, 0.0, 1.0)
        
        return img_wb
