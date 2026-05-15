import cv2
import numpy as np
from src.core.isp.nodes.base_node import BaseISPNode
from src.models.isp_config import SplitterConfig, RegionConfig

class SplitterNode(BaseISPNode):
    """
    Splits the image into regions, processes each region with its own sub-pipeline,
    and alpha-blends the results back into the original image.
    """
    def process(self, image: np.ndarray, config: SplitterConfig, pipeline_engine=None, **kwargs) -> np.ndarray:
        if not pipeline_engine:
            print("Warning: SplitterNode requires a pipeline_engine to process sub-pipelines.")
            return image
            
        if config.mode == "auto_diptych" and not config.regions:
            # Auto-detect!
            rects = find_frame_rects(image)
            from src.models.isp_config import PipelineConfig
            # Populate regions automatically with empty pipelines
            config.regions = [RegionConfig(bbox=r, pipeline=PipelineConfig()) for r in rects]
            
        if not config.regions:
            return image
            
        output_image = image.copy()
        feather = config.feathering
        
        for region in config.regions:
            x, y, w, h = region.bbox
            
            # Ensure bounds
            bg_h, bg_w = output_image.shape[:2]
            x, y = max(0, x), max(0, y)
            w, h = min(w, bg_w - x), min(h, bg_h - y)
            
            if w <= 0 or h <= 0:
                continue
                
            crop = output_image[y:y+h, x:x+w].copy()
            
            # Run sub-pipeline
            # Assuming pipeline_engine has a method run_pipeline_on_image
            processed_crop = pipeline_engine.run_pipeline_on_image(crop, region.pipeline)
            
            # Blend back
            self._blend_crop(output_image, processed_crop, (x, y, w, h), feather)
            
        return output_image
        
    def _blend_crop(self, bg_img: np.ndarray, processed_crop: np.ndarray, bbox: tuple, feather: int) -> None:
        x, y, w, h = bbox
        feather = max(3, feather)
        if feather % 2 == 0: feather += 1
        
        mask = np.zeros((h, w), dtype=np.float32)
        if h > feather * 2 and w > feather * 2:
            mask[feather:-feather, feather:-feather] = 1.0
            mask = cv2.GaussianBlur(mask, (feather, feather), 0)
        else:
            mask[:, :] = 1.0
            
        mask_3d = np.expand_dims(mask, axis=-1)
        
        bg_crop_f = bg_img[y:y+h, x:x+w].astype(np.float32)
        processed_f = processed_crop.astype(np.float32)
        
        blended = processed_f * mask_3d + bg_crop_f * (1.0 - mask_3d)
        bg_img[y:y+h, x:x+w] = blended.astype(bg_img.dtype)

def find_frame_rects(image: np.ndarray) -> list[tuple]:
    """
    Auto-detects the left and right bounding boxes of a diptych.
    """
    from src.core.isp.nodes.geometry import get_tilt_angle_from_strip
    # In a real pipeline, we'd separate strip lines detection, but here we can just do a fast threshold
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
            if x + wb // 2 < w // 2: left_raw_list.append((x, y, wb, hb))
            else: right_raw_list.append((x, y, wb, hb))

    def get_bounding_rect(rects):
        if not rects: return None
        min_x, min_y = min([r[0] for r in rects]), min([r[1] for r in rects])
        max_x, max_y = max([r[0] + r[2] for r in rects]), max([r[1] + r[3] for r in rects])
        return (min_x, min_y, max_x - min_x, max_y - min_y)

    left_raw = get_bounding_rect(left_raw_list)
    right_raw = get_bounding_rect(right_raw_list)
    
    unified_h = min(max(int(h * 0.94), left_raw[3] if left_raw else 0, right_raw[3] if right_raw else 0), h)
    unified_y, base_w = (h - unified_h) // 2, int(unified_h * (18.0 / 24.0))
    margin = int(w * 0.002) 
    
    # We estimate strip_left and strip_right based on true center
    true_center_x = w // 2
    strip_left = true_center_x - 10
    strip_right = true_center_x + 10
    
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
