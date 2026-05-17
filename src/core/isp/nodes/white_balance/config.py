from typing import Literal
from pydantic import Field
from src.models.isp_config import BaseNodeConfig, NodeMetadata, UIElementConfig, UIType, GroupType, TagType, List

class ManualWBConfig(BaseNodeConfig):
    node_type: Literal["ManualWBNode"] = "ManualWBNode"
    scale_r: float = Field(default=1.0, ge=0.0, le=5.0)
    scale_g: float = Field(default=1.0, ge=0.0, le=5.0)
    scale_b: float = Field(default=1.0, ge=0.0, le=5.0)

    @classmethod
    def get_ui_schema(cls) -> List[UIElementConfig]:
        return [
            UIElementConfig(type=UIType.BUTTON, name="Выбрать пипеткой", action_id="activate_picker"),
            UIElementConfig(type=UIType.BUTTON, name="Сбросить баланс", action_id="reset_wb"),
            UIElementConfig(type=UIType.SLIDER, name="Усиление R", field="scale_r", min=0.0, max=5.0),
            UIElementConfig(type=UIType.SLIDER, name="Усиление G", field="scale_g", min=0.0, max=5.0),
            UIElementConfig(type=UIType.SLIDER, name="Усиление B", field="scale_b", min=0.0, max=5.0),
        ]

    @classmethod
    def get_node_info(cls) -> NodeMetadata:
        return NodeMetadata(
            title="Ручной баланс белого",
            description_short="Настройка баланса белого по пипетке.",
            description_long="Позволяет кликнуть пипеткой по области, которая должна быть нейтрально-серой, и автоматически вычисляет множители цветовых каналов для компенсации паразитных оттенков. Также позволяет корректировать ползунки вручную.",
            author="Гоша",
            url="",
            tags=[TagType.COLOR, TagType.WHITE_BALANCE],
            group=GroupType.COLOR
        )
