from typing import List
from src.models.isp_config import BaseNodeConfig, NodeMetadata, UIElementConfig, UIType, GroupType, TagType

class MonochromeConfig(BaseNodeConfig):
    node_type: str = "MonochromeNode"
    auto_levels: bool = True
    brightness: float = 0.0     
    contrast: float = 1.0       
    black_point: float = 0.0    
    white_point: float = 1.0    
    shadows: float = 0.0        
    highlights: float = 0.0     
    hdr: float = 0.0            
    sharpness: float = 0.0      

    @classmethod
    def get_ui_schema(cls) -> List[UIElementConfig]:
        return [
            UIElementConfig(type=UIType.CHECKBOX, name="Авто Уровни", field="auto_levels"),
            UIElementConfig(type=UIType.SLIDER, name="Яркость", field="brightness", min=-1.0, max=1.0),
            UIElementConfig(type=UIType.SLIDER, name="Контраст", field="contrast", min=0.0, max=3.0),
            UIElementConfig(type=UIType.SLIDER, name="Точка черного", field="black_point", min=0.0, max=1.0),
            UIElementConfig(type=UIType.SLIDER, name="Точка белого", field="white_point", min=0.0, max=1.0),
            UIElementConfig(type=UIType.SLIDER, name="Тени", field="shadows", min=-1.0, max=1.0),
            UIElementConfig(type=UIType.SLIDER, name="Света", field="highlights", min=-1.0, max=1.0),
            UIElementConfig(type=UIType.SLIDER, name="HDR (Clarity)", field="hdr", min=0.0, max=2.0),
            UIElementConfig(type=UIType.SLIDER, name="Резкость", field="sharpness", min=0.0, max=3.0),
        ]

    @classmethod
    def get_node_info(cls) -> NodeMetadata:
        return NodeMetadata(
            title="ЧБ Редактор", 
            group=GroupType.EXPOSURE,
            tags=[TagType.LIGHT, TagType.CONTRAST, TagType.SHADOWS, TagType.BLACK_POINT]
        )
