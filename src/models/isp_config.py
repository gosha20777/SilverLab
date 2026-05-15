from typing import Literal, Annotated, Union, ForwardRef
from pydantic import BaseModel, Field

class BaseNodeConfig(BaseModel):
    node_type: str
    enabled: bool = True

class ExposureConfig(BaseNodeConfig):
    node_type: Literal["ExposureNode"] = "ExposureNode"
    value: float = Field(default=0.0, ge=-2.0, le=2.0, description="Экспозиция")

class BlackClipConfig(BaseNodeConfig):
    node_type: Literal["BlackClipNode"] = "BlackClipNode"
    clip_percent: float = Field(default=0.1, ge=0.0, le=2.0, description="Отсечение черного (%)")

class WhitePatchConfig(BaseNodeConfig):
    node_type: Literal["WhitePatchNode"] = "WhitePatchNode"
    patch_percent: float = Field(default=99.5, ge=95.0, le=100.0, description="Порог белого (%)")

class ContrastStretchConfig(BaseNodeConfig):
    node_type: Literal["ContrastStretchNode"] = "ContrastStretchNode"
    # No extra parameters needed for simple linear stretch

class AdaptiveGammaConfig(BaseNodeConfig):
    node_type: Literal["AdaptiveGammaNode"] = "AdaptiveGammaNode"
    target_lum: float = Field(default=0.5, ge=0.1, le=0.9, description="Целевая яркость")
    min_gamma: float = Field(default=0.6, ge=0.1, le=1.0)
    max_gamma: float = Field(default=1.5, ge=1.0, le=3.0)

class VibranceConfig(BaseNodeConfig):
    node_type: Literal["VibranceNode"] = "VibranceNode"
    strength: float = Field(default=0.3, ge=0.0, le=2.0, description="Vibrance (Умная насыщенность)")

class RotationConfig(BaseNodeConfig):
    node_type: Literal["RotationNode"] = "RotationNode"
    angle: float = Field(default=0.0, ge=-90.0, le=90.0, description="Угол поворота")

PipelineConfigRef = ForwardRef('PipelineConfig')

class RegionConfig(BaseModel):
    bbox: tuple[int, int, int, int] = (0, 0, 0, 0) # x, y, w, h
    pipeline: PipelineConfigRef

class SplitterConfig(BaseNodeConfig):
    node_type: Literal["SplitterNode"] = "SplitterNode"
    mode: Literal["auto_diptych", "manual"] = "auto_diptych"
    feathering: int = Field(default=15, ge=0, le=100, description="Растушевка (px)")
    regions: list[RegionConfig] = Field(default_factory=list)

# Polymorphic list of nodes using Pydantic's discriminator
AnyNodeConfig = Annotated[
    Union[
        ExposureConfig, 
        BlackClipConfig, 
        WhitePatchConfig, 
        ContrastStretchConfig, 
        AdaptiveGammaConfig, 
        VibranceConfig,
        RotationConfig,
        SplitterConfig
    ],
    Field(discriminator='node_type')
]

import yaml

class PipelineConfig(BaseModel):
    """
    Represents a full ISP Pipeline configuration (Preset).
    """
    name: str = "Default Profile"
    nodes: list[AnyNodeConfig] = Field(default_factory=list)

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
