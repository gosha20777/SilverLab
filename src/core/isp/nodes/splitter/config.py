from typing import Literal
from pydantic import Field
from src.models.isp_config import BaseNodeConfig, RegionConfig

class SplitterConfig(BaseNodeConfig):
    node_type: Literal["SplitterNode"] = "SplitterNode"
    mode: Literal["auto_diptych", "manual"] = "auto_diptych"
    feathering: int = Field(default=15, ge=0, le=100)
    regions: list[RegionConfig] = Field(default_factory=list)
    apply_rotation: bool = True
    target_angle: float = -0.7
    angle_tolerance: float = 0.3
    current_angle: float = 0.0
    final_crop: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)

    @classmethod
    def get_ui_schema(cls) -> list[dict]:
        return [
            {"type": "checkbox", "name": "Авто-поворот", "field": "apply_rotation"},
            {"type": "slider", "name": "Целевой угол", "field": "target_angle", "min": -5.0, "max": 5.0},
            {"type": "slider", "name": "Допуск угла", "field": "angle_tolerance", "min": 0.0, "max": 2.0},
            {"type": "slider", "name": "Текущий угол", "field": "current_angle", "min": -5.0, "max": 5.0},
            {"type": "slider", "name": "Растушевка", "field": "feathering", "min": 0, "max": 50},
            {"type": "custom", "renderer": "splitter_regions"}
        ]

    @classmethod
    def get_node_info(cls) -> dict:
        return {
            "title": "Диптих (Splitter)",
            "description_short": "Автоматическое разделение полукадров.",
            "description_long": "Мощный алгоритм для пленочных полукадров (Half-Frame). Автоматически находит разделительную межкадровую полосу, вычисляет угол ее наклона, выравнивает кадр и обрезает пустые края. Разделяет изображение на 2 независимых региона, каждый из которых может иметь свой собственный независимый конвейер фильтров (ISP).",
            "author": "Гоша",
            "url": "",
            "tags": ["Сложные фильтры", "Полукадр", "Диптих", "Обрезка", "Автоматизация"],
            "group": "Геометрия и Кадрирование"
        }
