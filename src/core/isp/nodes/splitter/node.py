import cv2
import numpy as np
import math
from typing import Optional, Tuple, List

from src.core.isp.nodes.base_node import BaseISPNode
from src.models.isp_config import RegionConfig, PipelineConfig
from .config import SplitterConfig


class SplitterNode(BaseISPNode):
    """
    Diptych node: detects strip, calculates tilt, rotates, splits regions, processes and blends.
    """

    def process(
        self,
        image: np.ndarray,
        config: SplitterConfig,
        pipeline_engine=None,
        is_export: bool = False,
        **kwargs
    ) -> np.ndarray:
        if not pipeline_engine:
            print("Warning: SplitterNode requires a pipeline_engine to process sub-pipelines.")
            return image

        bg_h, bg_w = image.shape[:2]

        # 1. Auto-Detection (if enabled)
        if config.mode == "auto_diptych":
            self._run_auto_detection(image, config)

        # 2. Rotation
        working_image = image
        if config.apply_rotation and config.current_angle != 0.0:
            M = cv2.getRotationMatrix2D((bg_w // 2, bg_h // 2), config.current_angle, 1.0)
            working_image = cv2.warpAffine(
                image, M, (bg_w, bg_h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
            )

        # 3. Regions Detection (if enabled)
        if config.mode == "auto_diptych":
            self._update_regions_auto(working_image, config)

        if not config.regions:
            return working_image

        # 4. Processing Regions
        output_image = working_image.copy()
        feather = config.feathering

        for region in config.regions:
            if getattr(region, "enabled", True):
                self._process_region(output_image, working_image, region, pipeline_engine, feather, is_export)

        # 5. Final Crop (only applied when exporting)
        if is_export:
            output_image = self._apply_final_crop(output_image, config)

        return output_image

    def _run_auto_detection(self, image: np.ndarray, config: SplitterConfig) -> None:
        """Runs the auto detection for strip and tilt angle."""
        left_pts, right_pts, _, _ = self._get_strip_lines(image)
        config.current_angle = self._get_tilt_angle(
            left_pts, right_pts, config.target_angle, config.angle_tolerance
        )

    def _update_regions_auto(self, image: np.ndarray, config: SplitterConfig) -> None:
        """Detects region boundaries automatically based on the strip position."""
        bg_h, bg_w = image.shape[:2]
        left_pts_rot, right_pts_rot, true_center_x_rot, _ = self._get_strip_lines(image)
        
        strip_left = int(np.median([p[0] for p in left_pts_rot])) if left_pts_rot else true_center_x_rot - 10
        strip_right = int(np.median([p[0] for p in right_pts_rot])) if right_pts_rot else true_center_x_rot + 10

        rects_px = self._find_frame_rects(image, strip_left, strip_right)
        rects = [(r[0] / bg_w, r[1] / bg_h, r[2] / bg_w, r[3] / bg_h) for r in rects_px]

        # Ensure we have enough region configs
        while len(config.regions) < len(rects):
            config.regions.append(RegionConfig(bbox=(0.0, 0.0, 0.0, 0.0), pipeline=PipelineConfig()))

        for i, r in enumerate(rects):
            config.regions[i].bbox = r

        if len(rects_px) == 2:
            self._calculate_final_crop(rects_px, bg_w, bg_h, config)

    def _calculate_final_crop(
        self, rects_px: List[Tuple[int, int, int, int]], bg_w: int, bg_h: int, config: SplitterConfig
    ) -> None:
        """Calculates the bounding box that encompasses both diptych frames."""
        xl, yl, wl, hl = rects_px[0]
        xr, yr, wr, hr = rects_px[1]
        
        top, bottom = min(yl, yr), max(yl + hl, yr + hr)
        left, right = xl, xr + wr

        # Apply 2% margins
        if top > bg_h * 0.04:
            top = int(bg_h * 0.02)
        if bottom < bg_h * 0.96:
            bottom = bg_h - int(bg_h * 0.02)
        if left > bg_w * 0.04:
            left = int(bg_w * 0.02)
        if right < bg_w * 0.96:
            right = bg_w - int(bg_w * 0.02)

        config.final_crop = (left / bg_w, top / bg_h, (right - left) / bg_w, (bottom - top) / bg_h)

    def _process_region(
        self, 
        output_image: np.ndarray, 
        working_image: np.ndarray, 
        region: RegionConfig, 
        pipeline_engine, 
        feather: int,
        is_export: bool
    ) -> None:
        """Extracts, processes, and blends a single region."""
        bg_h, bg_w = working_image.shape[:2]
        nx, ny, nw, nh = region.bbox
        x, y = int(nx * bg_w), int(ny * bg_h)
        w, h = int(nw * bg_w), int(nh * bg_h)

        x, y = max(0, x), max(0, y)
        w, h = min(w, bg_w - x), min(h, bg_h - y)

        if w <= 0 or h <= 0:
            return

        crop = working_image[y : y + h, x : x + w].copy()
        processed_crop = pipeline_engine.run_pipeline_on_image(crop, region.pipeline, is_export=is_export)
        self._blend_crop(output_image, processed_crop, (x, y, w, h), feather)

    def _apply_final_crop(self, image: np.ndarray, config: SplitterConfig) -> np.ndarray:
        """Applies the final crop coordinates to the image."""
        bg_h, bg_w = image.shape[:2]
        fx, fy, fw, fh = config.final_crop
        l, t = max(0, int(fx * bg_w)), max(0, int(fy * bg_h))
        r, b = min(bg_w, int((fx + fw) * bg_w)), min(bg_h, int((fy + fh) * bg_h))
        
        if l < r and t < b:
            return image[t:b, l:r]
        return image

    def _blend_crop(self, bg_img: np.ndarray, processed_crop: np.ndarray, bbox: tuple, feather: int) -> None:
        """Blends a processed region back into the main image using Gaussian feathering."""
        x, y, w, h = bbox
        feather = max(3, feather)
        if feather % 2 == 0:
            feather += 1

        mask = np.zeros((h, w), dtype=np.float32)
        if h > feather * 2 and w > feather * 2:
            mask[feather:-feather, feather:-feather] = 1.0
            mask = cv2.GaussianBlur(mask, (feather, feather), 0)
        else:
            mask[:, :] = 1.0

        mask_3d = np.expand_dims(mask, axis=-1)

        bg_crop_f = bg_img[y : y + h, x : x + w].astype(np.float32)
        processed_f = processed_crop.astype(np.float32)

        blended = processed_f * mask_3d + bg_crop_f * (1.0 - mask_3d)
        bg_img[y : y + h, x : x + w] = np.clip(blended, 0, 65535).astype(bg_img.dtype)

    @staticmethod
    def _get_strip_lines(image: np.ndarray) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]], int, int]:
        """Detects the central dividing strip in a diptych image."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if gray.dtype == np.uint16:
            gray_8u = (gray / 256).astype(np.uint8)
        else:
            gray_8u = gray
            if gray_8u.dtype == np.float32:
                gray_8u = (gray_8u * 255).astype(np.uint8)

        h, w = gray_8u.shape
        blurred = cv2.GaussianBlur(gray_8u, (15, 15), 0)

        mid_start, mid_end = int(w * 0.35), int(w * 0.65)
        y_margin = int(h * 0.1)
        center_roi = blurred[y_margin : h - y_margin, mid_start:mid_end]
        
        col_profile = np.mean(center_roi, axis=0)
        col_profile = cv2.GaussianBlur(col_profile.astype(np.float32).reshape(1, -1), (15, 1), 0).flatten()
        true_center_x = mid_start + np.argmin(col_profile)

        mask = np.zeros((h + 2, w + 2), np.uint8)
        flags = 4 | (255 << 8) | cv2.FLOODFILL_FIXED_RANGE | cv2.FLOODFILL_MASK_ONLY
        cv2.floodFill(blurred, mask, (int(true_center_x), h // 2), 255, loDiff=12, upDiff=12, flags=flags)
        strip_mask = mask[1:-1, 1:-1]

        max_penetration = int(w * 0.1)
        strip_mask[:, : max(0, int(true_center_x - max_penetration))] = 0
        strip_mask[:, min(w, int(true_center_x + max_penetration)) :] = 0

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        strip_mask = cv2.morphologyEx(strip_mask, cv2.MORPH_CLOSE, kernel)

        left_pts, right_pts = [], []
        for y in range(0, h, 10):
            row = strip_mask[y, :]
            nz = np.nonzero(row)[0]
            if len(nz) > 0:
                left_pts.append((nz[0], y))
                right_pts.append((nz[-1], y))
                
        return left_pts, right_pts, true_center_x, h

    @staticmethod
    def _get_tilt_angle(left_pts: List, right_pts: List, target: float, tolerance: float) -> float:
        """Calculates the best tilt angle given the detected strip edge points."""
        def get_angle(pts):
            if len(pts) < 10:
                return None
            [vx, vy, _, _] = cv2.fitLine(np.array(pts, dtype=np.int32), cv2.DIST_L2, 0, 0.01, 0.01)
            if abs(vy[0]) < 1e-5:
                return None
            if vy[0] < 0:
                vx[0], vy[0] = -vx[0], -vy[0]
            return math.degrees(math.atan2(vx[0], vy[0]))

        ang_l, ang_r = get_angle(left_pts), get_angle(right_pts)
        best_angle = target

        if ang_l is not None and ang_r is not None:
            best_angle = ang_l if abs(ang_l - target) < abs(ang_r - target) else ang_r
        elif ang_l is not None:
            best_angle = ang_l
        elif ang_r is not None:
            best_angle = ang_r

        if best_angle < target - tolerance or best_angle > target + tolerance:
            best_angle = target
            
        return best_angle

    @staticmethod
    def _find_frame_rects(image: np.ndarray, strip_left: int, strip_right: int) -> List[Tuple[int, int, int, int]]:
        """Finds bounding boxes for the actual image frames (ignoring dark borders)."""
        if image.dtype == np.uint16:
            gray_8u = (cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) / 256).astype(np.uint8)
        else:
            gray_8u = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if gray_8u.dtype == np.float32:
                gray_8u = (gray_8u * 255).astype(np.uint8)

        h, w = gray_8u.shape
        blurred = cv2.GaussianBlur(gray_8u, (35, 35), 0)
        otsu_val, _ = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, thresh = cv2.threshold(blurred, max(15, otsu_val * 0.2), 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 30))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        left_raw_list, right_raw_list = [], []
        for cnt in contours:
            x, y, wb, hb = cv2.boundingRect(cnt)
            if wb > w * 0.05 and hb > h * 0.1:
                if x + wb // 2 < w // 2:
                    left_raw_list.append((x, y, wb, hb))
                else:
                    right_raw_list.append((x, y, wb, hb))

        def get_bounding_rect(rects):
            if not rects:
                return None
            min_x, min_y = min([r[0] for r in rects]), min([r[1] for r in rects])
            max_x, max_y = max([r[0] + r[2] for r in rects]), max([r[1] + r[3] for r in rects])
            return (min_x, min_y, max_x - min_x, max_y - min_y)

        left_raw = get_bounding_rect(left_raw_list)
        right_raw = get_bounding_rect(right_raw_list)

        unified_h = min(max(int(h * 0.94), left_raw[3] if left_raw else 0, right_raw[3] if right_raw else 0), h)
        unified_y, base_w = (h - unified_h) // 2, int(unified_h * (18.0 / 24.0))
        margin = int(w * 0.002)

        raw_rects = []
        if left_raw:
            lw = min(max(left_raw[2] if left_raw else 0, base_w), int(w * 0.48))
            raw_rects.append((strip_left + margin - lw, unified_y, lw, unified_h))
        else:
            raw_rects.append((strip_left + margin - base_w, unified_y, base_w, unified_h))

        if right_raw:
            rw = min(max(right_raw[2] if right_raw else 0, base_w), int(w * 0.48))
            raw_rects.append((strip_right - margin, unified_y, rw, unified_h))
        else:
            raw_rects.append((strip_right - margin, unified_y, base_w, unified_h))

        safe_rects = []
        for x, y, wb, hb in raw_rects:
            x1, y1 = max(0, int(x)), max(0, int(y))
            x2, y2 = min(w, int(x + wb)), min(h, int(y + hb))
            safe_rects.append((x1, y1, max(0, x2 - x1), max(0, y2 - y1)))

        return safe_rects
