import numpy as np
import cv2
import math
from pydantic import BaseModel
from src.core.isp.nodes.base_node import BaseISPNode
from .config import AdaptiveGammaConfig

class AdaptiveGammaNode(BaseISPNode):
    """
    ISP Node for Adaptive Gamma correction (pulls midtones).
    """
    def process(self, image: np.ndarray, config: AdaptiveGammaConfig, **kwargs) -> np.ndarray:
        if not isinstance(config, AdaptiveGammaConfig):
            raise ValueError("Expected AdaptiveGammaConfig")
            
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_lum = np.mean(gray)
        
        if mean_lum < 0.01:
            mean_lum = 0.01
            
        gamma = math.log(config.target_lum) / math.log(mean_lum)
        gamma = np.clip(gamma, config.min_gamma, config.max_gamma)
        
        img_gamma = np.power(image, gamma)
        return np.clip(img_gamma, 0.0, 1.0).astype(image.dtype)
