from typing import Any, ForwardRef, List
from pydantic import BaseModel, Field, field_validator
import yaml
from .ui import UIElementConfig, NodeMetadata

class BaseNodeConfig(BaseModel):
    node_type: str
    enabled: bool = True

    @classmethod
    def get_ui_schema(cls) -> List[UIElementConfig]:
        """
        Returns a list of UIElementConfig models defining the UI for this node.
        """
        return []

    @classmethod
    def get_node_info(cls) -> NodeMetadata:
        """
        Returns strongly typed NodeMetadata for the UI Picker.
        """
        return NodeMetadata(title=cls.__name__)

PipelineConfigRef = ForwardRef('PipelineConfig')

class RegionConfig(BaseModel):
    source_file: str = ""  # Path to source file. Empty = current file (filled by SplitterNode).
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0) # Normalized x, y, w, h
    pipeline: PipelineConfigRef
    enabled: bool = True

class PipelineConfig(BaseModel):
    """
    Represents a full ISP Pipeline configuration (Preset).
    """
    name: str = "Default Profile"
    nodes: list[Any] = Field(default_factory=list)

    @field_validator('nodes', mode='before')
    @classmethod
    def parse_nodes(cls, v: Any) -> Any:
        from src.core.isp.plugin_manager import plugin_manager
        if not isinstance(v, list):
            return v
            
        parsed_nodes = []
        for n in v:
            if isinstance(n, dict) and 'node_type' in n:
                config_cls = plugin_manager.get_config_class(n['node_type'])
                if config_cls:
                    parsed_nodes.append(config_cls(**n))
                else:
                    print(f"Warning: Unknown node type {n['node_type']}")
                    parsed_nodes.append(n)
            else:
                parsed_nodes.append(n)
        return parsed_nodes

    def to_yaml(self, file_path: str) -> None:
        """Saves the pipeline configuration to a YAML file."""
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, allow_unicode=True, sort_keys=False)

    @classmethod
    def from_yaml(cls, file_path: str) -> 'PipelineConfig':
        """Loads a pipeline configuration from a YAML file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)
