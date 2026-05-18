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

        # 3. Layout & Regions Detection (if enabled)
        if config.mode == "auto_diptych":
            self._update_layout_and_regions(working_image, config, pipeline_engine)

        if not config.layout_rects or not config.regions:
            return working_image

        # 4. Processing Regions: iterate layout_rects (slots) paired with regions (content)
        output_image = working_image.copy()
        feather = config.feathering

        for i, dest_rect in enumerate(config.layout_rects):
            if i < len(config.regions) and config.regions[i].enabled:
                self._process_region(
                    output_image, working_image, dest_rect, config.regions[i],
                    pipeline_engine, feather, is_export
                )

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

    def _update_layout_and_regions(
        self, image: np.ndarray, config: SplitterConfig, pipeline_engine
    ) -> None:
        """Detects region boundaries and writes them to layout_rects. Initializes regions only if needed."""
        bg_h, bg_w = image.shape[:2]
        left_pts_rot, right_pts_rot, true_center_x_rot, _ = self._get_strip_lines(image)
        
        strip_left = int(np.median([p[0] for p in left_pts_rot])) if left_pts_rot else true_center_x_rot - 10
        strip_right = int(np.median([p[0] for p in right_pts_rot])) if right_pts_rot else true_center_x_rot + 10

        rects_px = self._find_frame_rects(image, strip_left, strip_right)
        rects_norm = [(r[0] / bg_w, r[1] / bg_h, r[2] / bg_w, r[3] / bg_h) for r in rects_px]

        # Write detected slots to layout_rects
        config.layout_rects = rects_norm

        # Initialize regions ONLY if count doesn't match (preserve user swaps)
        current_file = getattr(pipeline_engine, 'current_file_path', '')
        if len(config.regions) != len(rects_norm):
            config.regions = [
                RegionConfig(
                    source_file=current_file,
                    bbox=r,
                    pipeline=PipelineConfig(),
                )
                for r in rects_norm
            ]
        else:
            # Update source_file for regions that still have empty source_file
            for region in config.regions:
                if not region.source_file:
                    region.source_file = current_file

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

        # Apply 2% margins (force to edges unless regions exceed them)
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
        dest_rect: tuple[float, float, float, float],
        region: RegionConfig, 
        pipeline_engine, 
        feather: int,
        is_export: bool
    ) -> None:
        """Extracts content from source, applies Crop-to-Fill, processes, and blends into dest slot."""
        # 1. Determine source image:
        #    - For native regions (source == current file): use working_image (already rotated)
        #    - For external regions: use ImageProvider (raw from disk)
        current_file = getattr(pipeline_engine, 'current_file_path', '')
        is_native = (region.source_file == current_file) or (not region.source_file)

        if is_native:
            source_img = working_image
        elif pipeline_engine and pipeline_engine.image_provider and region.source_file:
            source_img = pipeline_engine.image_provider.get_image(
                region.source_file, is_proxy=not is_export
            )
        else:
            source_img = working_image

        # 2. Extract crop from source by region.bbox
        sh, sw = source_img.shape[:2]
        sx, sy, s_w, s_h = region.bbox
        x1, y1 = int(round(sx * sw)), int(round(sy * sh))
        x2, y2 = int(round((sx + s_w) * sw)), int(round((sy + s_h) * sh))
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(sw, x2), min(sh, y2)

        if x2 <= x1 or y2 <= y1:
            return

        crop = source_img[y1:y2, x1:x2].copy()  # .copy() protects ImageProvider cache

        # 3. Crop-to-Fill: fit crop into dest_rect preserving aspect ratio
        oh, ow = output_image.shape[:2]
        dx, dy, dw, dh = dest_rect
        target_w = int(round(dw * ow))
        target_h = int(round(dh * oh))
        dest_x = int(round(dx * ow))
        dest_y = int(round(dy * oh))
        crop_h, crop_w = crop.shape[:2]

        if target_w <= 0 or target_h <= 0:
            return

        if crop_w != target_w or crop_h != target_h:
            src_ratio = crop_w / max(crop_h, 1)
            dst_ratio = target_w / max(target_h, 1)

            if src_ratio > dst_ratio:
                # Crop wider than slot -> scale by height, trim width
                scale = target_h / max(crop_h, 1)
                scaled_w = max(1, int(crop_w * scale))
                scaled = cv2.resize(crop, (scaled_w, target_h), interpolation=cv2.INTER_LANCZOS4)
                excess = scaled.shape[1] - target_w
                crop = scaled[:, excess // 2: excess // 2 + target_w]
            else:
                # Crop narrower than slot -> scale by width, trim height
                scale = target_w / max(crop_w, 1)
                scaled_h = max(1, int(crop_h * scale))
                scaled = cv2.resize(crop, (target_w, scaled_h), interpolation=cv2.INTER_LANCZOS4)
                excess = scaled.shape[0] - target_h
                crop = scaled[excess // 2: excess // 2 + target_h, :]

        # 4. Run sub-pipeline color correction
        processed_crop = pipeline_engine.run_pipeline_on_image(crop, region.pipeline, is_export=is_export)

        # 5. Blend into output_image at dest_rect coordinates
        self._blend_crop(output_image, processed_crop, (dest_x, dest_y, target_w, target_h), feather)

    def _apply_final_crop(self, image: np.ndarray, config: SplitterConfig) -> np.ndarray:
        """Applies the final crop coordinates to the image."""
        bg_h, bg_w = image.shape[:2]
        fx, fy, fw, fh = config.final_crop
        l, t = max(0, int(round(fx * bg_w))), max(0, int(round(fy * bg_h)))
        r, b = min(bg_w, int(round((fx + fw) * bg_w))), min(bg_h, int(round((fy + fh) * bg_h)))
        
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
