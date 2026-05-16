from typing import Any, ForwardRef, List
from pydantic import BaseModel, Field, field_validator
import yaml
from enum import Enum

class UIType(str, Enum):
    SLIDER = 'slider'
    CHECKBOX = 'checkbox'
    LABEL = 'label'
    CUSTOM = 'custom'

class GroupType(str, Enum):
    EXPOSURE = 'exposure_and_light'
    COLOR = 'color_correction'
    GEOMETRY = 'geometry_and_crop'
    CREATIVE = 'creative_filters'
    MISC = 'misc'

    @property
    def label(self) -> str:
        labels = {
            "exposure_and_light": "Экспозиция и Свет",
            "color_correction": "Цветокоррекция",
            "geometry_and_crop": "Геометрия и Кадрирование",
            "creative_filters": "Креативные фильтры",
            "misc": "Разное"
        }
        return labels.get(self.value, self.value)

class TagType(str, Enum):
    LIGHT = 'light'
    BRIGHTNESS = 'brightness'
    EXPOSURE = 'exposure'
    BASIC = 'basic_correction'
    BLACK_POINT = 'black_point'
    CONTRAST = 'contrast'
    SHADOWS = 'shadows'
    COLOR = 'color'
    WHITE_BALANCE = 'white_balance'
    HISTOGRAM = 'histogram'
    GAMMA = 'gamma'
    MIDTONES = 'midtones'
    CURVES = 'curves'
    SATURATION = 'saturation'
    GEOMETRY = 'geometry'
    ROTATION = 'rotation'
    TRANSFORM = 'transform'
    COMPLEX = 'complex_filters'
    HALF_FRAME = 'half_frame'
    DIPTYCH = 'diptych'
    CROP = 'crop'
    AUTOMATION = 'automation'

    @property
    def label(self) -> str:
        labels = {
            "light": "Свет", "brightness": "Яркость", "exposure": "Экспозиция",
            "basic_correction": "Базовая коррекция", "black_point": "Точка черного",
            "contrast": "Контраст", "shadows": "Тени", "color": "Цвет",
            "white_balance": "Баланс белого", "histogram": "Гистограмма",
            "gamma": "Гамма", "midtones": "Средние тона", "curves": "Кривые",
            "saturation": "Насыщенность", "geometry": "Геометрия",
            "rotation": "Поворот", "transform": "Трансформация",
            "complex_filters": "Сложные фильтры", "half_frame": "Полукадр",
            "diptych": "Диптих", "crop": "Обрезка", "automation": "Автоматизация"
        }
        return labels.get(self.value, self.value)

class UIElementConfig(BaseModel):
    type: UIType
    name: str = ""
    field: str = ""
    min: float = 0.0
    max: float = 0.0
    text: str = ""
    renderer: str = ""

class NodeMetadata(BaseModel):
    title: str
    description_short: str = ""
    description_long: str = ""
    author: str = "SilverLab Team"
    url: str = ""
    tags: List[TagType] = Field(default_factory=list)
    group: GroupType = GroupType.MISC

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
