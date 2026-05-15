import numpy as np
import cv2
from pydantic import BaseModel
from src.core.isp.nodes.base_node import BaseISPNode
from src.models.isp_config import WhitePatchConfig

class WhitePatchNode(BaseISPNode):
    """
    ISP Node for White Balance using the White Patch algorithm.
    """
    def process(self, image: np.ndarray, config: WhitePatchConfig, **kwargs) -> np.ndarray:
        if not isinstance(config, WhitePatchConfig):
            raise ValueError("Expected WhitePatchConfig")
            
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        white_threshold = np.percentile(gray, config.patch_percent)
        mask = (gray >= white_threshold).astype(np.uint8)
        
        if cv2.countNonZero(mask) == 0:
            return image.copy()
            
        mean_b, mean_g, mean_r, _ = cv2.mean(image, mask=mask)
        target = max(mean_b, mean_g, mean_r) + 1e-6
        mean_b += 1e-6
        mean_g += 1e-6
        mean_r += 1e-6

        img_wb = image.copy()
        img_wb[:, :, 0] = np.clip(img_wb[:, :, 0] * (target / mean_b), 0.0, 1.0)
        img_wb[:, :, 1] = np.clip(img_wb[:, :, 1] * (target / mean_g), 0.0, 1.0)
        img_wb[:, :, 2] = np.clip(img_wb[:, :, 2] * (target / mean_r), 0.0, 1.0)
        
        return img_wb
