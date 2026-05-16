import importlib
import inspect
from src.core.isp.nodes.base_node import BaseISPNode
from src.models.isp_config import BaseNodeConfig

module = importlib.import_module("src.core.isp.nodes.exposure")
print("Module:", module)
for attr_name in dir(module):
    attr = getattr(module, attr_name)
    if inspect.isclass(attr):
        print(f"Class: {attr.__name__}, Module: {attr.__module__}")
