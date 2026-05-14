import numpy as np
from src.core.isp.nodes.exposure import ExposureNode
from src.models.frame_container import FrameContainer


class ISPPipeline:
    """
    Orchestrator that applies a chain of ISP nodes to an image.
    """
    def __init__(self) -> None:
        self.exposure_node = ExposureNode()

    def process_container(self, container: FrameContainer) -> None:
        """
        Passes the raw image through the active nodes and updates the container's cache.

        Args:
            container (FrameContainer): The data model.
        """
        processed = self.exposure_node.process(
            container.raw_image, 
            exposure_value=container.exposure_value
        )
        container.update_cache(processed)
