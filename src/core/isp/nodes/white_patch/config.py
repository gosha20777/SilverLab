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
