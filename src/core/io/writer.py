import cv2
import numpy as np

def save_image(image_array: np.ndarray, file_path: str) -> bool:
    """
    Saves the provided image array to the specified file path.
    """
    try:
        # cv2 expects BGR for saving, but if it's Grayscale it handles it automatically
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            # Our numpy array is BGR since we read with cv2 and haven't converted 
            # the raw_image/cached_image color space, only for display.
            save_array = image_array
        else:
            save_array = image_array
            
        return cv2.imwrite(file_path, save_array)
    except Exception as e:
        print(f"Error saving image: {e}")
        return False
