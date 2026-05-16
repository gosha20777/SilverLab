import cv2
import numpy as np
import math
from src.core.isp.nodes.base_node import BaseISPNode
from .config import RotationConfig

class RotationNode(BaseISPNode):
    """
    Applies rotation to the image.
    """
    def process(self, image: np.ndarray, config: RotationConfig, **kwargs) -> np.ndarray:
        out = image
        
        if config.flip_h:
            out = cv2.flip(out, 1)
        if config.flip_v:
            out = cv2.flip(out, 0)
            
        if config.angle_90 == 90:
            out = cv2.rotate(out, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif config.angle_90 == 180:
            out = cv2.rotate(out, cv2.ROTATE_180)
        elif config.angle_90 == 270:
            out = cv2.rotate(out, cv2.ROTATE_90_CLOCKWISE)
            
        if config.angle != 0.0:
            h, w = out.shape[:2]
            M = cv2.getRotationMatrix2D((w // 2, h // 2), config.angle, 1.0)
            out = cv2.warpAffine(out, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            
        return out
