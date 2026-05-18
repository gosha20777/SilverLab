from typing import Literal
from pydantic import Field
from src.models.isp_config import BaseNodeConfig, NodeMetadata, UIElementConfig, UIType, GroupType, TagType, List, RegionConfig

class SplitterConfig(BaseNodeConfig):
    node_type: Literal["SplitterNode"] = "SplitterNode"
    mode: Literal["auto_diptych", "manual"] = "auto_diptych"
    feathering: int = Field(default=15, ge=0, le=100)
    regions: list[RegionConfig] = Field(default_factory=list)
    layout_rects: list[tuple[float, float, float, float]] = Field(default_factory=list)
    apply_rotation: bool = True
    target_angle: float = 0.0
    angle_tolerance: float = 0.3
    current_angle: float = 0.0
    final_crop: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)
    @classmethod
    def get_ui_schema(cls) -> List[UIElementConfig]:
        return [
            UIElementConfig(type=UIType.CHECKBOX, name="Авто-поворот", field="apply_rotation"),
            UIElementConfig(type=UIType.SLIDER, name="Целевой угол", field="target_angle", min=-5.0, max=5.0),
            UIElementConfig(type=UIType.SLIDER, name="Допуск угла", field="angle_tolerance", min=0.0, max=2.0),
            UIElementConfig(type=UIType.SLIDER, name="Текущий угол", field="current_angle", min=-5.0, max=5.0),
            UIElementConfig(type=UIType.SLIDER, name="Растушевка", field="feathering", min=0, max=50),
            UIElementConfig(type=UIType.CUSTOM, renderer="splitter_regions")
        ]

    @classmethod
    def get_node_info(cls) -> NodeMetadata:
        return NodeMetadata(
            title="Диптих (Splitter)",
            description_short="Автоматическое разделение полукадров.",
            description_long="Мощный алгоритм для пленочных полукадров (Half-Frame). Автоматически находит разделительную межкадровую полосу, вычисляет угол ее наклона, выравнивает кадр и обрезает пустые края. Разделяет изображение на 2 независимых региона, каждый из которых может иметь свой собственный независимый конвейер фильтров (ISP).",
            author="Гоша",
            url="",
            tags=[TagType.COMPLEX, TagType.HALF_FRAME, TagType.DIPTYCH, TagType.CROP, TagType.AUTOMATION],
            group=GroupType.GEOMETRY
        )
