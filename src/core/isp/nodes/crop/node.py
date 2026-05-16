import numpy as np
from src.core.isp.nodes.base_node import BaseISPNode
from .config import CropConfig

class CropNode(BaseISPNode):
    """
    Applies the crop based on the bounding box.
    Aspect ratio enforcement is handled by the UI during interaction.
    """
    def process(
        self,
        image: np.ndarray,
        config: CropConfig,
        pipeline_engine=None,
        is_export: bool = False,
        **kwargs
    ) -> np.ndarray:
        bg_h, bg_w = image.shape[:2]
        nx, ny, nw, nh = config.bbox
        
        if not is_export:
            return image
            
        # In export mode, the bounding box must be exactly applied
        x, y = int(round(nx * bg_w)), int(round(ny * bg_h))
        w, h = int(round(nw * bg_w)), int(round(nh * bg_h))
        
        x, y = max(0, x), max(0, y)
        w, h = min(w, bg_w - x), min(h, bg_h - y)
        
        if w <= 0 or h <= 0:
            return image
            
        return image[y:y+h, x:x+w].copy()
