from typing import Literal
from pydantic import Field
from src.models.isp_config import BaseNodeConfig, NodeMetadata, UIElementConfig, UIType, GroupType, TagType, List

class BlackClipConfig(BaseNodeConfig):
    node_type: Literal["BlackClipNode"] = "BlackClipNode"
    clip_percent: float = Field(default=0.1, ge=0.0, le=2.0)
    @classmethod
    def get_ui_schema(cls) -> List[UIElementConfig]:
        return [
            UIElementConfig(type=UIType.SLIDER, name="Отсечение черного (%)", field="clip_percent", min=0.0, max=2.0)
        ]

    @classmethod
    def get_node_info(cls) -> NodeMetadata:
        return NodeMetadata(
            title="Отсечение черного (Black Clip)",
            description_short="Устанавливает точку черного.",
            description_long="Алгоритм находит самый темный пиксель на основе заданного процента (по умолчанию 0.1%) и сдвигает гистограмму так, чтобы этот пиксель стал абсолютно черным. Устраняет вуаль и повышает общий микроконтраст.",
            author="Гоша",
            url="",
            tags=[TagType.BLACK_POINT, TagType.CONTRAST, TagType.BASIC, TagType.SHADOWS],
            group=GroupType.EXPOSURE
        )
