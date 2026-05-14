import cv2
import numpy as np
from PySide6.QtGui import QImage, QPixmap


def numpy_to_qpixmap(image_array: np.ndarray) -> QPixmap:
    """
    Converts a NumPy array to a QPixmap for efficient GUI rendering.

    Args:
        image_array (np.ndarray): Original image (8-bit or 16-bit).

    Returns:
        QPixmap: Ready-to-render PySide6 Pixmap.
    """
    if image_array is None or image_array.size == 0:
        return QPixmap()

    if image_array.dtype == np.uint16:
        display_array = (image_array / 256.0).astype(np.uint8)
    elif image_array.dtype == np.float32:
        # Scale float [0.0, 1.0] to uint8 [0, 255]
        display_array = np.clip(image_array * 255.0, 0, 255).astype(np.uint8)
    else:
        display_array = image_array.astype(np.uint8)

    height, width = display_array.shape[:2]

    if len(display_array.shape) == 2:
        bytes_per_line = width
        q_image = QImage(
            display_array.data, width, height, bytes_per_line, QImage.Format_Grayscale8
        )
    elif len(display_array.shape) == 3 and display_array.shape[2] == 3:
        rgb_array = cv2.cvtColor(display_array, cv2.COLOR_BGR2RGB)
        bytes_per_line = 3 * width
        q_image = QImage(
            rgb_array.data, width, height, bytes_per_line, QImage.Format_RGB888
        )
        q_image.ndarray = rgb_array  # type: ignore 
    else:
        raise ValueError("Unsupported array shape for QPixmap conversion.")

    return QPixmap.fromImage(q_image)
