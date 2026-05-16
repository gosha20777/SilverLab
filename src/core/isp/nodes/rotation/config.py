from typing import Literal
from pydantic import Field
from src.models.isp_config import BaseNodeConfig, NodeMetadata, UIElementConfig, UIType, GroupType, TagType, List

class RotationConfig(BaseNodeConfig):
    node_type: Literal["RotationNode"] = "RotationNode"
    angle: float = Field(default=0.0, ge=-90.0, le=90.0)
    @classmethod
    def get_ui_schema(cls) -> List[UIElementConfig]:
        return [
            UIElementConfig(type=UIType.SLIDER, name="Угол", field="angle", min=-15.0, max=15.0)
        ]

    @classmethod
    def get_node_info(cls) -> NodeMetadata:
        return NodeMetadata(
            title="Свободный поворот (Rotation)",
            description_short="Поворот изображения на заданный угол.",
            description_long="Позволяет вращать холст на угол от -90 до +90 градусов вокруг центра кадра. Используется интерполяция INTER_LINEAR для минимизации потерь качества.",
            author="Гоша",
            url="",
            tags=[TagType.GEOMETRY, TagType.ROTATION, TagType.TRANSFORM],
            group=GroupType.GEOMETRY
        )
