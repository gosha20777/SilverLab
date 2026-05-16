from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QSlider, 
    QPushButton, QHBoxLayout, QFileDialog, QMenu, QCheckBox
)
from PySide6.QtGui import QCursor
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
        add_btn.clicked.connect(lambda: self._show_node_picker())
        top_layout.addWidget(add_btn)
        
        preset_layout = QHBoxLayout()
        load_btn = QPushButton("Загрузить пресет")
        load_btn.clicked.connect(self._load_preset)
        save_btn = QPushButton("Сохранить пресет")
        save_btn.clicked.connect(self._save_preset)
        
        preset_layout.addWidget(load_btn)
        preset_layout.addWidget(save_btn)
        top_layout.addLayout(preset_layout)
        
        apply_all_btn = QPushButton("Применить ко всем")
        apply_all_btn.clicked.connect(self.controller.apply_to_all)
        top_layout.addWidget(apply_all_btn)
        
        self.main_layout.addLayout(top_layout)
        self.main_layout.addSpacing(10)

    def _connect_signals(self) -> None:
        self.controller.pipeline_changed.connect(self._render_pipeline)

    def _load_preset(self) -> None:
        if not self.controller.sequence.active_container: return
        file_path, _ = QFileDialog.getOpenFileName(self, "Загрузить пресет", "", "YAML (*.yaml *.yml)")
        if file_path:
            try:
                new_config = PipelineConfig.from_yaml(file_path)
                self.controller.sequence.active_container.pipeline_config = new_config
                self.controller.pipeline_changed.emit()
                self.controller._trigger_pipeline(is_interactive=False)
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
        self._render_node_list(self.nodes_layout, config, is_root=True)

    def _render_node_list(self, layout, pipeline_config, is_root=True, root_index=0):
        for i, node_conf in enumerate(pipeline_config.nodes):
            actual_root_idx = i if is_root else root_index
            section = self._build_node_ui(node_conf, pipeline_config, i, actual_root_idx)
            layout.addWidget(section)

    def _build_node_ui(self, node_config, parent_pipeline, local_index: int, root_index: int):
        from src.views.widgets.node_settings_section import NodeSettingsSection
        return NodeSettingsSection(node_config, parent_pipeline, local_index, root_index, self)

    def _show_node_picker(self, pipeline_config=None, root_index=0) -> None:
        if not self.controller.sequence.active_container:
            return
            
        dialog = NodePickerDialog(self)
        if dialog.exec():
            new_config = dialog.get_selected_config()
            if new_config:
                if pipeline_config is not None:
                    pipeline_config.nodes.append(new_config)
                    self.controller.pipeline_changed.emit()
                    self.controller._trigger_pipeline(start_node_index=root_index, is_interactive=False)
                else:
                    self.controller.add_node(new_config)
