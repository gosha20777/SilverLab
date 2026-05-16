from typing import Literal
from pydantic import Field
from src.models.isp_config import BaseNodeConfig, NodeMetadata, UIElementConfig, UIType, GroupType, TagType, List

class RotationConfig(BaseNodeConfig):
    node_type: Literal["RotationNode"] = "RotationNode"
    angle: float = Field(default=0.0, ge=-45.0, le=45.0)
    angle_90: int = Field(default=0) # 0, 90, 180, 270
    flip_h: bool = Field(default=False)
    flip_v: bool = Field(default=False)
    
    @classmethod
    def get_ui_schema(cls) -> List[UIElementConfig]:
        return [
            UIElementConfig(type=UIType.BUTTON, name="Повернуть +90°", action_id="rotate_cw"),
            UIElementConfig(type=UIType.BUTTON, name="Повернуть -90°", action_id="rotate_ccw"),
            UIElementConfig(type=UIType.CHECKBOX, name="Отразить по горизонтали", field="flip_h"),
            UIElementConfig(type=UIType.CHECKBOX, name="Отразить по вертикали", field="flip_v"),
            UIElementConfig(type=UIType.SLIDER, name="Точный Угол", field="angle", min=-45.0, max=45.0),
            UIElementConfig(type=UIType.BUTTON, name="Инструмент Линейка", action_id="activate_ruler")
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
