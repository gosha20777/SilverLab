from abc import ABC, abstractmethod
import numpy as np


class BaseISPNode(ABC):
    """
    Abstract base class for all Image Signal Processing operations.
    """
    @abstractmethod
    def process(self, image: np.ndarray, **kwargs) -> np.ndarray:
        """
        Applies a specific mathematical transformation to the image array.

        Args:
            image (np.ndarray): The input image array.
            **kwargs: Parameters specific to the ISP node.

        Returns:
            np.ndarray: The processed image array.
        """
        pass
