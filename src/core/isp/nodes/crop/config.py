from typing import List, Tuple
from src.models.isp_config import BaseNodeConfig, NodeMetadata, UIElementConfig, UIType, GroupType, TagType

class CropConfig(BaseNodeConfig):
    node_type: str = "CropNode"
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0) # Normalized x, y, w, h
    aspect_ratio: str = "free" # "free", "1:1", "3:2", "2:3", "4:3", "3:4", "16:9"
    grid_type: str = "rule_of_thirds" # "none", "rule_of_thirds", "golden_ratio"

    @classmethod
    def get_ui_schema(cls) -> List[UIElementConfig]:
        return [
            UIElementConfig(
                type=UIType.COMBOBOX, 
                name="Соотношение сторон", 
                field="aspect_ratio",
                options=[
                    ("Свободное", "free"),
                    ("1:1 (Квадрат)", "1:1"),
                    ("3:2 (35mm)", "3:2"),
                    ("2:3 (Портрет 35mm)", "2:3"),
                    ("4:3 (Ср. формат)", "4:3"),
                    ("3:4 (Портрет ср. ф.)", "3:4"),
                    ("6:7 (Широкий ср. ф.)", "6:7"),
                    ("7:6 (Портрет 6:7)", "7:6"),
                    ("16:9 (Панорама)", "16:9"),
                ]
            ),
            UIElementConfig(
                type=UIType.COMBOBOX,
                name="Сетка (при кадрировании)",
                field="grid_type",
                options=[
                    ("Правило третей", "rule_of_thirds"),
                    ("Золотое сечение", "golden_ratio"),
                    ("Отключена", "none")
                ]
            ),
            UIElementConfig(
                type=UIType.LABEL,
                text="Выберите инструмент Crop (✂️) на панели\nинструментов холста для изменения области."
            )
        ]

    @classmethod
    def get_node_info(cls) -> NodeMetadata:
        return NodeMetadata(
            title="Кадрирование",
            description_short="Свободная и пропорциональная обрезка",
            description_long="Обрезает изображение. Поддерживает классические пропорции фотопленки и отображение направляющих сеток (правило третей, золотое сечение) при редактировании.",
            tags=[TagType.GEOMETRY, TagType.CROP],
            group=GroupType.GEOMETRY
        )
