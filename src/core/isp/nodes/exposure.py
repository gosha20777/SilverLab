import numpy as np
from src.core.isp.nodes.base_node import BaseISPNode


class ExposureNode(BaseISPNode):
    """
    ISP Node for adjusting image brightness (exposure).
    """
    def process(self, image: np.ndarray, exposure_value: float = 0.0, **kwargs) -> np.ndarray:
        """
        Adjusts the exposure of the image by multiplying the array values.

        Args:
            image (np.ndarray): The input 16-bit or 8-bit image array.
            exposure_value (float): The exposure shift (e.g., -2.0 to +2.0 EV).
            **kwargs: Ignored.

        Returns:
            np.ndarray: The exposure-adjusted image array.
        """
        if exposure_value == 0.0:
            return image.copy()
            
        multiplier = 2.0 ** exposure_value
        
        if image.dtype != np.float32:
            img_float = image.astype(np.float32)
        else:
            img_float = image.copy()
            
        img_float *= multiplier
        
        if image.dtype == np.uint16:
            np.clip(img_float, 0, 65535, out=img_float)
            return img_float.astype(np.uint16)
        elif image.dtype == np.uint8:
            np.clip(img_float, 0, 255, out=img_float)
            return img_float.astype(np.uint8)
            
        return img_float
