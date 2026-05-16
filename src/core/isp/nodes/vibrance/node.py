import numpy as np
import cv2
from pydantic import BaseModel
from src.core.isp.nodes.base_node import BaseISPNode
from .config import VibranceConfig

class VibranceNode(BaseISPNode):
    """
    ISP Node for smart saturation (Vibrance).
    """
    def process(self, image: np.ndarray, config: VibranceConfig, **kwargs) -> np.ndarray:
        if not isinstance(config, VibranceConfig):
            raise ValueError("Expected VibranceConfig")
            
        if config.strength == 0.0:
            return image.copy()
            
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        s_channel = hsv[:, :, 1]
        s_boost = s_channel + config.strength * (1.0 - s_channel) * s_channel
        hsv[:, :, 1] = np.clip(s_boost, 0.0, 1.0)
        
        img_vib = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        return np.clip(img_vib, 0.0, 1.0)
