import cv2
import numpy as np
from typing import Optional

def read_image(file_path: str) -> Optional[np.ndarray]:
    """
    Reads an image from disk using OpenCV, supporting 16-bit.
    """
    return cv2.imread(file_path, cv2.IMREAD_UNCHANGED)

def generate_thumbnail(file_path: str, max_size: int = 150) -> Optional[np.ndarray]:
    """
    Reads an image and quickly downscales it for thumbnail display.
    Optimized for speed to prevent blocking.
    """
    # Use standard imread for thumbnails, convert to 8-bit color
    img = cv2.imread(file_path, cv2.IMREAD_COLOR)
    if img is None:
        return None
        
    h, w = img.shape[:2]
    scale = max_size / max(h, w)
    
    if scale < 1.0:
        new_w, new_h = int(w * scale), int(h * scale)
        thumbnail = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        thumbnail = img
        
    return thumbnail
