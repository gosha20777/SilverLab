from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QSlider, QPushButton
from PySide6.QtCore import Qt
from src.controllers.main_controller import MainController
from src.views.widgets.collapsible import CollapsibleSection
from src.views.widgets.algorithm_selector import AlgorithmSelector


class InspectorPanel(QScrollArea):
    """
    The right panel containing collapsible sections for all ISP parameters.
    """
    def __init__(self, controller: MainController) -> None:
        super().__init__()
        self.controller = controller
        
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.main_container = QWidget()
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setAlignment(Qt.AlignTop)
        self.setWidget(self.main_container)
        
        self._build_sections()
        self._connect_signals()
        
    def _build_sections(self) -> None:
        # 1. Base Corrections Section
        base_section = CollapsibleSection("Базовые коррекции")
        base_layout = QVBoxLayout()
        
        self.exposure_label = QLabel("Экспозиция: 0.0")
        base_layout.addWidget(self.exposure_label)
        
        self.exposure_slider = QSlider(Qt.Horizontal)
        self.exposure_slider.setMinimum(-20)
        self.exposure_slider.setMaximum(20)
        self.exposure_slider.setValue(0)
        base_layout.addWidget(self.exposure_slider)
        
        base_section.set_content_layout(base_layout)
        self.main_layout.addWidget(base_section)
        
        # 2. White Balance (Algorithm Selector Example)
        wb_section = CollapsibleSection("Баланс Белого")
        wb_layout = QVBoxLayout()
        
        self.wb_selector = AlgorithmSelector()
        
        # Algo 1: Manual
        manual_widget = QWidget()
        ml = QVBoxLayout(manual_widget)
        ml.addWidget(QLabel("Температура"))
        ml.addWidget(QSlider(Qt.Horizontal))
        ml.addWidget(QLabel("Оттенок"))
        ml.addWidget(QSlider(Qt.Horizontal))
        self.wb_selector.add_algorithm("Manual (Ручной)", manual_widget)
        
        # Algo 2: Picker
        picker_widget = QWidget()
        pl = QVBoxLayout(picker_widget)
        pl.addWidget(QPushButton("Взять образец (Пипетка)"))
        self.wb_selector.add_algorithm("White Patch (По образцу)", picker_widget)
        
        # Algo 3: Gray World
        gw_widget = QWidget()
        gw_l = QVBoxLayout(gw_widget)
        gw_l.addWidget(QLabel("Автоматический алгоритм. Настроек нет."))
        self.wb_selector.add_algorithm("Gray World (Авто)", gw_widget)
        
        wb_layout.addWidget(self.wb_selector)
        wb_section.set_content_layout(wb_layout)
        self.main_layout.addWidget(wb_section)
        
        # 3. Geometry Section
        geom_section = CollapsibleSection("Геометрия")
        geom_layout = QVBoxLayout()
        self.align_button = QPushButton("Авто-выравнивание")
        geom_layout.addWidget(self.align_button)
        geom_section.set_content_layout(geom_layout)
        self.main_layout.addWidget(geom_section)
        
        # Add stretch at the end
        self.main_layout.addStretch()

    def _connect_signals(self) -> None:
        self.exposure_slider.valueChanged.connect(self._on_exposure_changed)
        
    def _on_exposure_changed(self, value: int) -> None:
        real_value = value / 10.0
        self.exposure_label.setText(f"Экспозиция: {real_value:.1f}")
        self.controller.on_exposure_value_changed(real_value)
