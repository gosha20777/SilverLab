from typing import Literal
from pydantic import Field
from src.models.isp_config import BaseNodeConfig

class WhitePatchConfig(BaseNodeConfig):
    node_type: Literal["WhitePatchNode"] = "WhitePatchNode"
    patch_percent: float = Field(default=99.5, ge=95.0, le=100.0)

    @classmethod
    def get_ui_schema(cls) -> list[dict]:
        return [
            {"type": "slider", "name": "Порог белого (%)", "field": "patch_percent", "min": 95.0, "max": 100.0}
        ]

    @classmethod
    def get_node_info(cls) -> dict:
        return {
            "title": "Баланс Белого (White Patch)",
            "description_short": "Автоматический баланс белого по светлым участкам.",
            "description_long": "Использует алгоритм White Patch (Идеальный отражатель). Находит самые светлые пиксели (верхние 0.5-5%) и выравнивает цветовые каналы так, чтобы этот участок стал нейтрально-белым. Отлично работает для устранения общих цветовых сдвигов от лампы сканера.",
            "author": "Гоша",
            "url": "https://en.wikipedia.org/wiki/Color_balance",
            "tags": ["Цвет", "Баланс белого", "ББ", "Цветокоррекция"],
            "group": "Цветокоррекция"
        }
