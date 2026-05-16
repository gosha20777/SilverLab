from typing import Any, ForwardRef
from pydantic import BaseModel, Field, field_validator
import yaml

class BaseNodeConfig(BaseModel):
    node_type: str
    enabled: bool = True

    @classmethod
    def get_ui_schema(cls) -> list[dict]:
        """
        Returns a list of dictionaries defining the UI for this node.
        Example: [{"type": "slider", "name": "Экспозиция", "field": "value", "min": -2.0, "max": 2.0}]
        """
        return []

    @classmethod
    def get_node_info(cls) -> dict:
        """
        Returns metadata about the node for the UI Picker.
        """
        return {
            "title": cls.__name__,
            "description_short": "",
            "description_long": "",
            "author": "SilverLab Team",
            "url": "",
            "tags": [],
            "group": "Разное"
        }

PipelineConfigRef = ForwardRef('PipelineConfig')

class RegionConfig(BaseModel):
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0) # Normalized x, y, w, h
    pipeline: PipelineConfigRef

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
            yaml.dump(self.model_dump(mode='json'), f, allow_unicode=True, sort_keys=False)

    @classmethod
    def from_yaml(cls, file_path: str) -> "PipelineConfig":
        """Loads a pipeline configuration from a YAML file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

# Resolve circular references
PipelineConfig.model_rebuild()
RegionConfig.model_rebuild()
