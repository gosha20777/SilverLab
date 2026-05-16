from typing import Literal
from pydantic import Field
from src.models.isp_config import BaseNodeConfig

class AdaptiveGammaConfig(BaseNodeConfig):
    node_type: Literal["AdaptiveGammaNode"] = "AdaptiveGammaNode"
    target_lum: float = Field(default=0.5, ge=0.1, le=0.9)
    min_gamma: float = Field(default=0.6, ge=0.1, le=1.0)
    max_gamma: float = Field(default=1.5, ge=1.0, le=3.0)

    @classmethod
    def get_ui_schema(cls) -> list[dict]:
        return [
            {"type": "slider", "name": "Целевая яркость", "field": "target_lum", "min": 0.1, "max": 0.9}
        ]

    @classmethod
    def get_node_info(cls) -> dict:
        return {
            "title": "Средние тона (Adaptive Gamma)",
            "description_short": "Адаптивная настройка средних тонов.",
            "description_long": "Алгоритм вычисляет среднюю яркость кадра и применяет логарифмическую кривую (Гамму), чтобы привести изображение к заданной Целевой яркости (по умолчанию 0.5). Позволяет быстро вытянуть недоэкспонированные тени или приглушить пересветы, не затрагивая точки черного и белого.",
            "author": "Гоша",
            "url": "",
            "tags": ["Гамма", "Средние тона", "Свет", "Кривые"],
            "group": "Экспозиция и Свет"
        }
