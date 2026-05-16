import numpy as np
import cv2
from pydantic import BaseModel
from src.core.isp.nodes.base_node import BaseISPNode
from .config import ContrastStretchConfig

class ContrastStretchNode(BaseISPNode):
    """
    ISP Node for linear contrast stretching.
    """
    def process(self, image: np.ndarray, config: ContrastStretchConfig, **kwargs) -> np.ndarray:
        if not isinstance(config, ContrastStretchConfig):
            raise ValueError("Expected ContrastStretchConfig")
            
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        max_lum = np.max(gray)
        
        if max_lum > 0:
            scale = 1.0 / max_lum
            img_stretched = np.clip(image * scale, 0.0, 1.0)
            return img_stretched
            
        return image.copy()
