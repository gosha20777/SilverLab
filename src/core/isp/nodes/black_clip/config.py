from typing import Literal
from pydantic import Field
from src.models.isp_config import BaseNodeConfig

class BlackClipConfig(BaseNodeConfig):
    node_type: Literal["BlackClipNode"] = "BlackClipNode"
    clip_percent: float = Field(default=0.1, ge=0.0, le=2.0)

    @classmethod
    def get_ui_schema(cls) -> list[dict]:
        return [
            {"type": "slider", "name": "Отсечение черного (%)", "field": "clip_percent", "min": 0.0, "max": 2.0}
        ]
