import numpy as np
import cv2
from src.core.isp.nodes.base_node import BaseISPNode
from .config import MonochromeConfig

class MonochromeNode(BaseISPNode):
    """
    ISP Node for comprehensive Black and White editing.
    Includes Auto-levels, Brightness, Contrast, Black/White point,
    Shadows, Highlights, HDR, and Sharpness.
    """
    def process(self, image: np.ndarray, config: MonochromeConfig, **kwargs) -> np.ndarray:
        if not isinstance(config, MonochromeConfig):
            raise ValueError("Expected MonochromeConfig")

        # 1. Convert to Gray (process in single channel to save time)
        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            gray = image
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 2. Auto Levels computation
        if config.auto_levels:
            # Find 0.5% and 99.5% percentiles to ignore dust/scratches
            bp = np.percentile(gray, 0.5)
            wp = np.percentile(gray, 99.5)
            
            # Update config (since it's passed by reference, UI will update)
            config.black_point = float(bp)
            config.white_point = float(wp)

        # Work in float32 for precision
        y = gray.astype(np.float32)

        # 3. Black Point and White Point (Levels)
        bp = config.black_point
        wp = config.white_point
        if wp <= bp:
            wp = bp + 1e-6
        y = (y - bp) / (wp - bp)
        y = np.clip(y, 0.0, 1.0)

        # 4. Brightness (Exposure equivalent)
        # Shift brightness, keeping values around midtones mostly linear
        if config.brightness != 0.0:
            y = y + config.brightness
            y = np.clip(y, 0.0, 1.0)

        # 5. Contrast (Stretch around 0.5)
        if config.contrast != 1.0:
            y = (y - 0.5) * config.contrast + 0.5
            y = np.clip(y, 0.0, 1.0)

        # 6. Shadows and Highlights (Curve adjustments)
        # Shadows: x + s * (1-x)^2 * x (lifts/darkens shadows)
        # Highlights: x + h * x^2 * (1-x) (lifts/darkens highlights)
        if config.shadows != 0.0 or config.highlights != 0.0:
            s = config.shadows
            h = config.highlights
            y = y + s * ((1.0 - y) ** 2) * y + h * (y ** 2) * (1.0 - y)
            y = np.clip(y, 0.0, 1.0)

        # 7. HDR Effect (Large Radius Unsharp Masking / Clarity)
        if config.hdr > 0.0:
            h_img, w_img = y.shape
            radius = min(w_img, h_img) * 0.02
            sigma = radius / 3.0
            if sigma >= 1.0:
                blur_hdr = cv2.GaussianBlur(y, (0, 0), sigmaX=sigma, sigmaY=sigma)
                y = y + config.hdr * (y - blur_hdr)
                y = np.clip(y, 0.0, 1.0)

        # 8. Sharpness (Small Radius Unsharp Masking)
        if config.sharpness > 0.0:
            blur_sharp = cv2.GaussianBlur(y, (0, 0), sigmaX=1.5, sigmaY=1.5)
            y = y + config.sharpness * (y - blur_sharp)
            y = np.clip(y, 0.0, 1.0)

        # 9. Convert back to 3-channel (so pipeline doesn't break)
        out_image = np.dstack((y, y, y))
        return out_image
