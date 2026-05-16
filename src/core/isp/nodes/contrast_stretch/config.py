from typing import Literal
from src.models.isp_config import BaseNodeConfig

class ContrastStretchConfig(BaseNodeConfig):
    node_type: Literal["ContrastStretchNode"] = "ContrastStretchNode"

    @classmethod
    def get_ui_schema(cls) -> list[dict]:
        return [
            {"type": "label", "text": "Линейное растяжение гистограммы.\nНастроек нет."}
        ]

    @classmethod
    def get_node_info(cls) -> dict:
        return {
            "title": "Линейный Контраст (Stretch)",
            "description_short": "Растяжение гистограммы от 0 до 1.",
            "description_long": "Максимально растягивает гистограмму изображения: самое темное место становится 0, а самое светлое — максимальным значением. Это повышает общий контраст снимка.",
            "author": "Гоша",
            "url": "https://en.wikipedia.org/wiki/Normalization_(image_processing)",
            "tags": ["Контраст", "Гистограмма", "Базовая коррекция"],
            "group": "Экспозиция и Свет"
        }
