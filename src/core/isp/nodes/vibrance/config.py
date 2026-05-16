from typing import Literal
from pydantic import Field
from src.models.isp_config import BaseNodeConfig

class VibranceConfig(BaseNodeConfig):
    node_type: Literal["VibranceNode"] = "VibranceNode"
    strength: float = Field(default=0.3, ge=0.0, le=2.0)

    @classmethod
    def get_ui_schema(cls) -> list[dict]:
        return [
            {"type": "slider", "name": "Vibrance (Умная насыщенность)", "field": "strength", "min": 0.0, "max": 2.0}
        ]

    @classmethod
    def get_node_info(cls) -> dict:
        return {
            "title": "Умная Насыщенность (Vibrance)",
            "description_short": "Усиливает блеклые цвета.",
            "description_long": "Увеличивает насыщенность изображения, но делает это 'умно': блеклые цвета усиливаются сильнее, а уже насыщенные цвета остаются почти без изменений. Это предотвращает кислотные пересветы (clipping) в цветовых каналах.",
            "author": "Гоша",
            "url": "",
            "tags": ["Цвет", "Насыщенность", "Цветокоррекция"],
            "group": "Цветокоррекция"
        }
