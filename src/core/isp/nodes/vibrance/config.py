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
