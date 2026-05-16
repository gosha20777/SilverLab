from enum import Enum

class UIType(str, Enum):
    SLIDER = 'slider'
    CHECKBOX = 'checkbox'
    LABEL = 'label'
    COMBOBOX = 'combobox'
    BUTTON = 'button'
    CUSTOM = 'custom'

class GroupType(str, Enum):
    EXPOSURE = 'exposure_and_light'
    COLOR = 'color_correction'
    GEOMETRY = 'geometry_and_crop'
    CREATIVE = 'creative_filters'
    MISC = 'misc'

    @property
    def label(self) -> str:
        labels = {
            "exposure_and_light": "Экспозиция и Свет",
            "color_correction": "Цветокоррекция",
            "geometry_and_crop": "Геометрия и Кадрирование",
            "creative_filters": "Креативные фильтры",
            "misc": "Разное"
        }
        return labels.get(self.value, self.value)

class TagType(str, Enum):
    LIGHT = 'light'
    BRIGHTNESS = 'brightness'
    EXPOSURE = 'exposure'
    BASIC = 'basic_correction'
    BLACK_POINT = 'black_point'
    CONTRAST = 'contrast'
    SHADOWS = 'shadows'
    COLOR = 'color'
    WHITE_BALANCE = 'white_balance'
    HISTOGRAM = 'histogram'
    GAMMA = 'gamma'
    MIDTONES = 'midtones'
    CURVES = 'curves'
    SATURATION = 'saturation'
    GEOMETRY = 'geometry'
    ROTATION = 'rotation'
    TRANSFORM = 'transform'
    COMPLEX = 'complex_filters'
    HALF_FRAME = 'half_frame'
    DIPTYCH = 'diptych'
    CROP = 'crop'
    AUTOMATION = 'automation'

    @property
    def label(self) -> str:
        labels = {
            "light": "Свет", "brightness": "Яркость", "exposure": "Экспозиция",
            "basic_correction": "Базовая коррекция", "black_point": "Точка черного",
            "contrast": "Контраст", "shadows": "Тени", "color": "Цвет",
            "white_balance": "Баланс белого", "histogram": "Гистограмма",
            "gamma": "Гамма", "midtones": "Средние тона", "curves": "Кривые",
            "saturation": "Насыщенность", "geometry": "Геометрия",
            "rotation": "Поворот", "transform": "Трансформация",
            "complex_filters": "Сложные фильтры", "half_frame": "Полукадр",
            "diptych": "Диптих", "crop": "Обрезка", "automation": "Автоматизация"
        }
        return labels.get(self.value, self.value)
