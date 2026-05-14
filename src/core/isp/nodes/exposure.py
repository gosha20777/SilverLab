import numpy as np
from pydantic import BaseModel
from src.core.isp.nodes.base_node import BaseISPNode
from src.models.isp_config import ExposureConfig


class ExposureNode(BaseISPNode):
    """
    ISP Node for adjusting image brightness (exposure).
    """
    def process(self, image: np.ndarray, config: BaseModel) -> np.ndarray:
        """
        Adjusts the exposure of the image by multiplying the array values.

        Args:
            image (np.ndarray): The input 16-bit or 8-bit image array.
            config (ExposureConfig): The configuration containing exposure_value.
        """
        if not isinstance(config, ExposureConfig):
            raise ValueError("Expected ExposureConfig")
            
        exposure_value = config.value
        
        if exposure_value == 0.0:
            return image.copy()
            
        multiplier = 2.0 ** exposure_value
        img_float = image * multiplier
        return np.clip(img_float, 0.0, 1.0)
