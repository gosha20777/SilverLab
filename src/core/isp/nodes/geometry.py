import cv2
import numpy as np
import math
from src.core.isp.nodes.base_node import BaseISPNode
from src.models.isp_config import RotationConfig

class RotationNode(BaseISPNode):
    """
    Applies rotation to the image.
    """
    def process(self, image: np.ndarray, config: RotationConfig, **kwargs) -> np.ndarray:
        if config.angle == 0.0:
            return image
            
        h, w = image.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), config.angle, 1.0)
        
        # Warp affine preserves dtype and channels
        return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

def get_tilt_angle_from_strip(image: np.ndarray) -> float:
    """
    Auto-detects the tilt angle of the film strip by finding the central black bar.
    Ported from diptich-cutter.
    """
    # Create 8-bit gray image for edge detection
    if image.dtype == np.uint16:
        gray_8u = (cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) / 256).astype(np.uint8)
    else:
        gray_8u = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if gray_8u.dtype == np.float32:
            gray_8u = (gray_8u * 255).astype(np.uint8)
            
    h, w = gray_8u.shape
    blurred = cv2.GaussianBlur(gray_8u, (15, 15), 0)

    # Find the darkest vertical column in the middle 30% of the image
    mid_start, mid_end = int(w * 0.35), int(w * 0.65)
    y_margin = int(h * 0.1)
    center_roi = blurred[y_margin:h-y_margin, mid_start:mid_end]
    col_profile = np.mean(center_roi, axis=0)
    col_profile = cv2.GaussianBlur(col_profile.astype(np.float32).reshape(1, -1), (15, 1), 0).flatten()
    true_center_x = mid_start + np.argmin(col_profile)

    # Flood fill the black strip
    mask = np.zeros((h + 2, w + 2), np.uint8)
    flags = 4 | (255 << 8) | cv2.FLOODFILL_FIXED_RANGE | cv2.FLOODFILL_MASK_ONLY
    cv2.floodFill(blurred, mask, (int(true_center_x), h // 2), 255, loDiff=12, upDiff=12, flags=flags)
    strip_mask = mask[1:-1, 1:-1]
    
    # Restrict to central area
    max_penetration = int(w * 0.1)
    strip_mask[:, :max(0, int(true_center_x - max_penetration))] = 0
    strip_mask[:, min(w, int(true_center_x + max_penetration)):] = 0

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    strip_mask = cv2.morphologyEx(strip_mask, cv2.MORPH_CLOSE, kernel)

    left_pts, right_pts = [], []
    for y in range(0, h, 10):
        row = strip_mask[y, :]
        nz = np.nonzero(row)[0]
        if len(nz) > 0:
            left_pts.append((nz[0], y))
            right_pts.append((nz[-1], y))
            
    def get_angle(pts):
        if len(pts) < 10: return None
        [vx, vy, _, _] = cv2.fitLine(np.array(pts, dtype=np.int32), cv2.DIST_L2, 0, 0.01, 0.01)
        if abs(vy[0]) < 1e-5: return None
        if vy[0] < 0: vx[0], vy[0] = -vx[0], -vy[0]
        return math.degrees(math.atan2(vx[0], vy[0]))

    ang_l, ang_r = get_angle(left_pts), get_angle(right_pts)
    target = 0.0
    best_angle = target

    if ang_l is not None and ang_r is not None:
        best_angle = ang_l if abs(ang_l - target) < abs(ang_r - target) else ang_r
    elif ang_l is not None: best_angle = ang_l
    elif ang_r is not None: best_angle = ang_r

    if best_angle < -2.0 or best_angle > 2.0:
        # Suspicious angle, probably not a real strip line
        best_angle = target
        
    return best_angle
