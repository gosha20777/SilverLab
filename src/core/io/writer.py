import cv2
import numpy as np

def save_image(image_array: np.ndarray, file_path: str) -> bool:
    """
    Saves the provided image array to the specified file path.
    """
    try:
        save_array = image_array
        
        # If float32, we must scale it back to an integer format for saving
        if image_array.dtype == np.float32:
            # Check extension to decide bit depth
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                save_array = np.clip(image_array * 255.0, 0, 255).astype(np.uint8)
            elif file_path.lower().endswith(('.tiff', '.tif')):
                save_array = np.clip(image_array * 65535.0, 0, 65535).astype(np.uint16)
            else:
                # Default fallback
                save_array = np.clip(image_array * 255.0, 0, 255).astype(np.uint8)
            
        return cv2.imwrite(file_path, save_array)
    except Exception as e:
        print(f"Error saving image: {e}")
        return False
