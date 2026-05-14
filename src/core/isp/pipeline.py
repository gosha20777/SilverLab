import numpy as np
from src.models.frame_container import FrameContainer
from src.core.isp.nodes.exposure import ExposureNode
from src.core.isp.nodes.black_clip import BlackClipNode
from src.core.isp.nodes.white_patch import WhitePatchNode
from src.core.isp.nodes.contrast_stretch import ContrastStretchNode
from src.core.isp.nodes.adaptive_gamma import AdaptiveGammaNode
from src.core.isp.nodes.vibrance import VibranceNode

# Mapping from Pydantic config node_type to actual implementation class
NODE_REGISTRY = {
    "ExposureNode": ExposureNode,
    "BlackClipNode": BlackClipNode,
    "WhitePatchNode": WhitePatchNode,
    "ContrastStretchNode": ContrastStretchNode,
    "AdaptiveGammaNode": AdaptiveGammaNode,
    "VibranceNode": VibranceNode,
}

class ISPPipeline:
    """
    Orchestrator that applies a chain of ISP nodes to an image based on its PipelineConfig.
    """
    def __init__(self) -> None:
        # Instantiate all stateless nodes once
        self.node_instances = {name: cls() for name, cls in NODE_REGISTRY.items()}

    def process_container(self, container: FrameContainer) -> None:
        """
        Passes the raw image through the active nodes configured in the container.

        Args:
            container (FrameContainer): The data model containing raw_image and pipeline_config.
        """
        img = container.raw_image.copy()
        
        # Iterate over the configuration to maintain specific order
        for node_config in container.pipeline_config.nodes:
            if not node_config.enabled:
                continue
                
            node = self.node_instances.get(node_config.node_type)
            if node:
                img = node.process(img, node_config)
                
        container.update_cache(img)
