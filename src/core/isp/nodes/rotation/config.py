from typing import Literal
from pydantic import Field
from src.models.isp_config import BaseNodeConfig

class RotationConfig(BaseNodeConfig):
    node_type: Literal["RotationNode"] = "RotationNode"
    angle: float = Field(default=0.0, ge=-90.0, le=90.0)

    @classmethod
    def get_ui_schema(cls) -> list[dict]:
        return [
            {"type": "slider", "name": "Угол поворота", "field": "angle", "min": -15.0, "max": 15.0}
        ]
