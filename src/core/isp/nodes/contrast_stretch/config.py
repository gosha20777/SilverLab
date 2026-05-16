from typing import Literal
from src.models.isp_config import BaseNodeConfig, NodeMetadata, UIElementConfig, UIType, GroupType, TagType, List

class ContrastStretchConfig(BaseNodeConfig):
    node_type: Literal["ContrastStretchNode"] = "ContrastStretchNode"
    @classmethod
    def get_ui_schema(cls) -> List[UIElementConfig]:
        return [
            UIElementConfig(type=UIType.LABEL, text="Линейное растяжение гистограммы.\nНастроек нет.")
        ]

    @classmethod
    def get_node_info(cls) -> NodeMetadata:
        return NodeMetadata(
            title="Линейный Контраст (Stretch)",
            description_short="Растяжение гистограммы от 0 до 1.",
            description_long="Максимально растягивает гистограмму изображения: самое темное место становится 0, а самое светлое — максимальным значением. Это повышает общий контраст снимка.",
            author="Гоша",
            url="https://en.wikipedia.org/wiki/Normalization_(image_processing)",
            tags=[TagType.CONTRAST, TagType.HISTOGRAM, TagType.BASIC],
            group=GroupType.EXPOSURE
        )
