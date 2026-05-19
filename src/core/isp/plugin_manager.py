import importlib
import inspect
import pkgutil
from typing import Dict, Type

class PluginManager:
    """
    Dynamically loads ISP nodes from the plugins directory.
    """
    def __init__(self):
        self.nodes: Dict[str, Type] = {}
        self.configs: Dict[str, Type] = {}
        
    def load_plugins(self, package_name: str = "src.core.isp.nodes"):
        try:
            package = importlib.import_module(package_name)
        except ImportError as e:
            print(f"PluginManager: Failed to import package {package_name}: {e}")
            return
            
        from src.core.isp.nodes.base_node import BaseISPNode
        from src.models.isp_config import BaseNodeConfig
        
        import sys
        
        if getattr(sys, 'frozen', False):
            # In PyInstaller, we explicitly import all nodes in __init__.py
            # So we can just inspect the package module directly
            for attr_name in dir(package):
                attr = getattr(package, attr_name)
                if inspect.isclass(attr):
                    if issubclass(attr, BaseISPNode) and attr is not BaseISPNode:
                        self.nodes[attr.__name__] = attr
                    elif issubclass(attr, BaseNodeConfig) and attr is not BaseNodeConfig:
                        node_type = attr.model_fields['node_type'].default
                        self.configs[node_type] = attr
            return

        modules_to_check = [(name, is_pkg) for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + ".")]

        for name, is_pkg in modules_to_check:
            if is_pkg:
                try:
                    module = importlib.import_module(name)
                    
                    # Search for Node class
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if inspect.isclass(attr) and attr.__module__.startswith(module.__name__):
                            if issubclass(attr, BaseISPNode) and attr is not BaseISPNode:
                                # In our architecture, the node class name corresponds to the config node_type
                                # e.g. ExposureNode
                                self.nodes[attr.__name__] = attr
                            elif issubclass(attr, BaseNodeConfig) and attr is not BaseNodeConfig:
                                # Extract node_type from the Pydantic field default
                                node_type = attr.model_fields['node_type'].default
                                self.configs[node_type] = attr
                except Exception as e:
                    print(f"Failed to load plugin {name}: {e}")

    def get_config_class(self, node_type: str) -> Type:
        return self.configs.get(node_type)

    def get_node_class(self, node_type: str) -> Type:
        return self.nodes.get(node_type)

    def get_all_node_types(self) -> list[str]:
        return list(self.nodes.keys())

plugin_manager = PluginManager()
