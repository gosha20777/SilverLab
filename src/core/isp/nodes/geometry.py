import cv2
import numpy as np
import math
from src.core.isp.nodes.base_node import BaseISPNode
from src.models.isp_config import RotationConfig

class RotationNode(BaseISPNode):
    """
    Applies rotation to the image.
    """
    def process(self, image: np.ndarray, config: RotationConfig, **kwargs) -> np.ndarray:
        if config.angle == 0.0:
            return image
            
        h, w = image.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), config.angle, 1.0)
        
        # Warp affine preserves dtype and channels
        return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
