from typing import List, Tuple, Optional
from pydantic import BaseModel, Field
from .enums import UIType, TagType, GroupType

class UIElementConfig(BaseModel):
    type: UIType
    name: str = ""
    field: str = ""
    min: float = 0.0
    max: float = 0.0
    text: str = ""
    renderer: str = ""
    options: List[Tuple[str, str]] = Field(default_factory=list)
    action_id: Optional[str] = None

class NodeMetadata(BaseModel):
    title: str
    description_short: str = ""
    description_long: str = ""
    author: str = "SilverLab Team"
    url: str = ""
    tags: List[TagType] = Field(default_factory=list)
    group: GroupType = GroupType.MISC
