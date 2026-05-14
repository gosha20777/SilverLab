from typing import Optional
import numpy as np
from src.models.isp_config import PipelineConfig

class SequenceItem:
    """
    Represents a single image item in the gallery sequence.
    Holds metadata, the thumbnail for the UI, and the specific ISP configuration for this image.
    Does NOT hold the heavy raw or cached images.
    """
    def __init__(self, file_path: str):
        self.file_path: str = file_path
        self.thumbnail: Optional[np.ndarray] = None
        self.pipeline_config: Optional[PipelineConfig] = None
        self.status: str = "pending"
