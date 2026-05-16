from typing import Literal
from src.models.isp_config import BaseNodeConfig

class ContrastStretchConfig(BaseNodeConfig):
    node_type: Literal["ContrastStretchNode"] = "ContrastStretchNode"

    @classmethod
    def get_ui_schema(cls) -> list[dict]:
        return [
            {"type": "label", "text": "Линейное растяжение гистограммы.\nНастроек нет."}
        ]
