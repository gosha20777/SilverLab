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
