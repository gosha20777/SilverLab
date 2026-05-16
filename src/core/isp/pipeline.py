import numpy as np
from src.models.frame_container import FrameContainer
from src.core.isp.plugin_manager import plugin_manager

class ISPPipeline:
    """
    Orchestrator that applies a chain of ISP nodes to an image based on its PipelineConfig.
    """
    def __init__(self) -> None:
        # Instantiate all stateless nodes once
        self.node_instances = {name: cls() for name, cls in plugin_manager.nodes.items()}
        self.registry = self.node_instances

    def run_pipeline_on_image(self, image: np.ndarray, pipeline_config, is_export: bool = False) -> np.ndarray:
        """
        Executes a nested sub-pipeline without proxy caching.
        """
        current_image = image.copy()
        for node_conf in pipeline_config.nodes:
            if not node_conf.enabled:
                continue
            
            node_type = node_conf.node_type
            if node_type in self.registry:
                node = self.registry[node_type]
                try:
                    current_image = node.process(current_image, node_conf, pipeline_engine=self, is_export=is_export)
                except Exception as e:
                    print(f"Error processing nested node {node_type}: {e}")
        return current_image

    def process_container(self, container: FrameContainer, is_proxy: bool = False, start_node_index: int = 0, is_export: bool = False) -> None:
        """
        Executes the ISP pipeline on the container's image.
        Supports proxy processing and intermediate node caching for fast real-time UI response.
        """
        # Create a shallow copy to prevent IndexError if the UI thread modifies the list mid-flight
        nodes_config = list(container.pipeline_config.nodes)
        
        if not nodes_config:
            # Empty pipeline
            img = container.raw_proxy.copy() if is_proxy else container.raw_image.copy()
            container.update_cache(img, is_proxy=is_proxy)
            if is_proxy:
                container.proxy_caches.clear()
            return
            
        # Decide starting image based on cache
        if start_node_index == 0:
            current_image = container.raw_proxy.copy() if is_proxy else container.raw_image.copy()
            if is_proxy:
                container.proxy_caches.clear()
        else:
            # Resume from proxy cache if available
            if is_proxy and start_node_index - 1 < len(container.proxy_caches):
                current_image = container.proxy_caches[start_node_index - 1].copy()
                # Truncate caches that will be recalculated
                container.proxy_caches = container.proxy_caches[:start_node_index]
            else:
                # Fallback to full recalculation
                current_image = container.raw_proxy.copy() if is_proxy else container.raw_image.copy()
                start_node_index = 0
                if is_proxy:
                    container.proxy_caches.clear()

        # Execute nodes
        for i in range(start_node_index, len(nodes_config)):
            node_conf = nodes_config[i]
            
            if not node_conf.enabled:
                if is_proxy:
                    container.proxy_caches.append(current_image.copy())
                continue
                
            node_type = node_conf.node_type
            if node_type in self.registry:
                node = self.registry[node_type]
                try:
                    current_image = node.process(current_image, node_conf, pipeline_engine=self, is_export=is_export)
                except Exception as e:
                    print(f"Error processing node {node_type}: {e}")
                    
            if is_proxy:
                container.proxy_caches.append(current_image.copy())
                
        container.update_cache(current_image, is_proxy=is_proxy)
