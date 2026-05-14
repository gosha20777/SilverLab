import numpy as np
import cv2
from pydantic import BaseModel
from src.core.isp.nodes.base_node import BaseISPNode
from src.models.isp_config import BlackClipConfig

class BlackClipNode(BaseISPNode):
    """
    ISP Node for cutting out shadows (film base fog).
    """
    def process(self, image: np.ndarray, config: BaseModel) -> np.ndarray:
        if not isinstance(config, BlackClipConfig):
            raise ValueError("Expected BlackClipConfig")
            
        if config.clip_percent <= 0.0:
            return image.copy()
            
        # Image is already float32 [0.0, 1.0]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        black_point = np.percentile(gray, config.clip_percent)
        
        img_clipped = np.clip(image - black_point, 0.0, 1.0)
        
        return img_clipped
