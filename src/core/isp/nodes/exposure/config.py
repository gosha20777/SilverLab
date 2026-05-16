from typing import Literal
from pydantic import Field
from src.models.isp_config import BaseNodeConfig

class ExposureConfig(BaseNodeConfig):
    node_type: Literal["ExposureNode"] = "ExposureNode"
    value: float = Field(default=0.0, ge=-2.0, le=2.0)

    @classmethod
    def get_ui_schema(cls) -> list[dict]:
        return [
            {"type": "slider", "name": "Экспозиция", "field": "value", "min": -2.0, "max": 2.0}
        ]
