from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QSlider, 
    QPushButton, QHBoxLayout, QFileDialog
)
from PySide6.QtCore import Qt
from src.controllers.main_controller import MainController
from src.views.widgets.collapsible import CollapsibleSection
from src.views.widgets.node_picker import NodePickerDialog
from src.models.isp_config import PipelineConfig

class InspectorPanel(QScrollArea):
    """
    The right panel acting as an ISP Pipeline Manager.
    Displays dynamic nodes and allows adding, removing, enabling, and reordering.
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
        
        self._build_top_controls()
        
        self.nodes_container = QWidget()
        self.nodes_layout = QVBoxLayout(self.nodes_container)
        self.nodes_layout.setAlignment(Qt.AlignTop)
        self.nodes_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.nodes_container)
        
        self.main_layout.addStretch()
        
        self._connect_signals()

    def _build_top_controls(self) -> None:
        top_layout = QVBoxLayout()
        
        add_btn = QPushButton("✚ Добавить фильтр")
        add_btn.setStyleSheet("font-weight: bold; padding: 6px;")
        add_btn.clicked.connect(self._show_node_picker)
        top_layout.addWidget(add_btn)
        
        preset_layout = QHBoxLayout()
        load_btn = QPushButton("Загрузить пресет")
        load_btn.clicked.connect(self._load_preset)
        save_btn = QPushButton("Сохранить пресет")
        save_btn.clicked.connect(self._save_preset)
        
        preset_layout.addWidget(load_btn)
        preset_layout.addWidget(save_btn)
        top_layout.addLayout(preset_layout)
        
        self.main_layout.addLayout(top_layout)
        self.main_layout.addSpacing(10)

    def _connect_signals(self) -> None:
        self.controller.pipeline_changed.connect(self._render_pipeline)

    def _show_node_picker(self) -> None:
        if not self.controller.sequence.active_container:
            return
            
        dialog = NodePickerDialog(self)
        if dialog.exec():
            new_config = dialog.get_selected_config()
            if new_config:
                self.controller.add_node(new_config)

    def _load_preset(self) -> None:
        if not self.controller.sequence.active_container: return
        file_path, _ = QFileDialog.getOpenFileName(self, "Загрузить пресет", "", "YAML (*.yaml *.yml)")
        if file_path:
            try:
                new_config = PipelineConfig.from_yaml(file_path)
                self.controller.sequence.active_container.pipeline_config = new_config
                self.controller.isp_pipeline.process_container(self.controller.sequence.active_container)
                self.controller.image_processed.emit(self.controller.sequence.active_container)
                self.controller.pipeline_changed.emit()
            except Exception as e:
                print(f"Error loading preset: {e}")

    def _save_preset(self) -> None:
        if not self.controller.sequence.active_container: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить пресет", "", "YAML (*.yaml)")
        if file_path:
            self.controller.sequence.active_container.pipeline_config.to_yaml(file_path)

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _render_pipeline(self) -> None:
        """Completely rebuilds the node cards based on the active PipelineConfig."""
        self._clear_layout(self.nodes_layout)
        
        if not self.controller.sequence.active_container:
            return
            
        config = self.controller.sequence.active_container.pipeline_config
        for i, node_conf in enumerate(config.nodes):
            section = self._build_node_ui(node_conf, i)
            self.nodes_layout.addWidget(section)

    def _build_node_ui(self, node_config, index: int) -> CollapsibleSection:
        node_type = node_config.node_type
        titles = {
            "ExposureNode": "Экспозиция",
            "BlackClipNode": "Срез теней (Black Clip)",
            "WhitePatchNode": "Баланс Белого (Авто)",
            "ContrastStretchNode": "Контраст",
            "AdaptiveGammaNode": "Средние тона (Adaptive Gamma)",
            "VibranceNode": "Насыщенность (Vibrance)"
        }
        
        section = CollapsibleSection(titles.get(node_type, node_type), start_collapsed=False)
        section.set_enabled_state(node_config.enabled)
        layout = QVBoxLayout()
        
        # Connect Controls
        section.enabled_changed.connect(lambda state, idx=index: self.controller.toggle_node(idx, state))
        section.move_up_requested.connect(lambda idx=index: self.controller.move_node(idx, -1))
        section.move_down_requested.connect(lambda idx=index: self.controller.move_node(idx, 1))
        section.delete_requested.connect(lambda idx=index: self.controller.delete_node(idx))

        # Sliders
        if node_type == "ExposureNode":
            self._create_slider(layout, "Сдвиг (EV)", -2.0, 2.0, node_config.value, index, "value")
        elif node_type == "BlackClipNode":
            self._create_slider(layout, "Срез (%)", 0.0, 2.0, node_config.clip_percent, index, "clip_percent")
        elif node_type == "WhitePatchNode":
            self._create_slider(layout, "Порог белого (%)", 95.0, 100.0, node_config.patch_percent, index, "patch_percent")
        elif node_type == "AdaptiveGammaNode":
            self._create_slider(layout, "Целевая яркость", 0.1, 0.9, node_config.target_lum, index, "target_lum")
        elif node_type == "VibranceNode":
            self._create_slider(layout, "Усилие", 0.0, 2.0, node_config.strength, index, "strength")
        elif node_type == "ContrastStretchNode":
            layout.addWidget(QLabel("Линейное растяжение гистограммы.\nНастроек нет."))
            
        section.set_content_layout(layout)
        return section

    def _create_slider(self, layout, name: str, min_val: float, max_val: float, current: float, index: int, field_name: str):
        label = QLabel(f"{name}: {current:.2f}")
        layout.addWidget(label)
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(100)
        
        initial_pos = int(((current - min_val) / (max_val - min_val)) * 100)
        slider.setValue(initial_pos)
        layout.addWidget(slider)
        
        def on_change(val):
            real_val = min_val + (val / 100.0) * (max_val - min_val)
            label.setText(f"{name}: {real_val:.2f}")
            self.controller.update_node_config(index, **{field_name: real_val})
            
        slider.valueChanged.connect(on_change)
