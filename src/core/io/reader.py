import cv2
import numpy as np
from typing import Optional

def read_image(file_path: str) -> Optional[np.ndarray]:
    """
    Reads an image from disk using OpenCV and immediately normalizes it
    to a float32 array in the range [0.0, 1.0] to prevent precision loss.
    """
    img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        return None
        
    # Standardize all inputs to 3-channel (BGR)
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif len(img.shape) == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
    if img.dtype == np.uint8:
        return img.astype(np.float32) / 255.0
    elif img.dtype == np.uint16:
        return img.astype(np.float32) / 65535.0
    elif img.dtype == np.float32:
        return img
    else:
        # Fallback for unexpected formats
        return img.astype(np.float32)

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
