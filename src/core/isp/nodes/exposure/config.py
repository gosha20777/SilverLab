from typing import Literal
from pydantic import Field
from src.models.isp_config import BaseNodeConfig, NodeMetadata, UIElementConfig, UIType, GroupType, TagType, List

class ExposureConfig(BaseNodeConfig):
    node_type: Literal["ExposureNode"] = "ExposureNode"
    value: float = Field(default=0.0, ge=-2.0, le=2.0)
    @classmethod
    def get_ui_schema(cls) -> List[UIElementConfig]:
        return [
            UIElementConfig(type=UIType.SLIDER, name="Сдвиг (EV)", field="value", min=-2.0, max=2.0)
        ]

    @classmethod
    def get_node_info(cls) -> NodeMetadata:
        return NodeMetadata(
            title="Экспозиция (Exposure)",
            description_short="Линейный сдвиг экспозиции (EV).",
            description_long="Позволяет изменять общую яркость изображения в шагах экспозиции (EV). Математически это умножение линейных данных на 2^EV. Полезно для точной подстройки яркости без изменения контраста.",
            author="Гоша",
            url="",
            tags=[TagType.LIGHT, TagType.BRIGHTNESS, TagType.EXPOSURE, TagType.BASIC],
            group=GroupType.EXPOSURE
        )
