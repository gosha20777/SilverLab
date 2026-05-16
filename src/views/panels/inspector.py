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

    def _build_node_ui(self, node_config, parent_pipeline, local_index: int, root_index: int) -> CollapsibleSection:
        node_type = node_config.node_type
        titles = {
            "ExposureNode": "Экспозиция",
            "BlackClipNode": "Срез теней (Black Clip)",
            "WhitePatchNode": "Баланс Белого (Авто)",
            "ContrastStretchNode": "Контраст",
            "AdaptiveGammaNode": "Средние тона (Adaptive Gamma)",
            "VibranceNode": "Насыщенность (Vibrance)",
            "RotationNode": "Поворот (Геометрия)",
            "SplitterNode": "Диптих (Разделение кадра)"
        }
        
        section = CollapsibleSection(titles.get(node_type, node_type), start_collapsed=False)
        section.set_enabled_state(node_config.enabled)
        layout = QVBoxLayout()
        
        # Connect Controls
        def on_toggle(state):
            node_config.enabled = state
            self.controller._trigger_pipeline(start_node_index=root_index, is_interactive=False)
            
        def on_delete():
            parent_pipeline.nodes.pop(local_index)
            self.controller.pipeline_changed.emit()
            self.controller._trigger_pipeline(start_node_index=root_index, is_interactive=False)
            
        def on_move(direction):
            new_idx = local_index + direction
            if 0 <= new_idx < len(parent_pipeline.nodes):
                nodes = parent_pipeline.nodes
                nodes[local_index], nodes[new_idx] = nodes[new_idx], nodes[local_index]
                self.controller.pipeline_changed.emit()
                self.controller._trigger_pipeline(start_node_index=root_index if root_index <= new_idx else new_idx, is_interactive=False)

        section.enabled_changed.connect(on_toggle)
        section.move_up_requested.connect(lambda: on_move(-1))
        section.move_down_requested.connect(lambda: on_move(1))
        section.delete_requested.connect(on_delete)

        # Sliders
        if node_type == "ExposureNode":
            self._create_slider(layout, "Сдвиг (EV)", -2.0, 2.0, node_config.value, node_config, "value", root_index)
        elif node_type == "BlackClipNode":
            self._create_slider(layout, "Срез (%)", 0.0, 2.0, node_config.clip_percent, node_config, "clip_percent", root_index)
        elif node_type == "WhitePatchNode":
            self._create_slider(layout, "Порог белого (%)", 95.0, 100.0, node_config.patch_percent, node_config, "patch_percent", root_index)
        elif node_type == "AdaptiveGammaNode":
            self._create_slider(layout, "Целевая яркость", 0.1, 0.9, node_config.target_lum, node_config, "target_lum", root_index)
        elif node_type == "VibranceNode":
            self._create_slider(layout, "Усилие", 0.0, 2.0, node_config.strength, node_config, "strength", root_index)
        elif node_type == "ContrastStretchNode":
            layout.addWidget(QLabel("Линейное растяжение гистограммы.\nНастроек нет."))
        elif node_type == "RotationNode":
            self._create_slider(layout, "Угол", -15.0, 15.0, node_config.angle, node_config, "angle", root_index)
        elif node_type == "SplitterNode":
            cb = QCheckBox("Авто-поворот")
            cb.setChecked(node_config.apply_rotation)
            cb.stateChanged.connect(lambda state, c=node_config: self._on_checkbox_changed(c, "apply_rotation", state))
            layout.addWidget(cb)
            
            self._create_slider(layout, "Целевой угол", -5.0, 5.0, node_config.target_angle, node_config, "target_angle", root_index)
            self._create_slider(layout, "Допуск угла", 0.0, 2.0, node_config.angle_tolerance, node_config, "angle_tolerance", root_index)
            self._create_slider(layout, "Текущий угол", -5.0, 5.0, node_config.current_angle, node_config, "current_angle", root_index)
            self._create_slider(layout, "Растушевка", 0, 50, node_config.feathering, node_config, "feathering", root_index)
            # Render spoilers for regions if they exist
            if node_config.regions:
                for r_idx, region in enumerate(node_config.regions):
                    region_group = CollapsibleSection(f"Регион {r_idx + 1}", start_collapsed=True)
                    region_layout = QVBoxLayout()
                    self._render_node_list(region_layout, region.pipeline, is_root=False, root_index=root_index)
                    
                    # Add node button for this region
                    add_btn = QPushButton(f"+ Добавить фильтр (Регион {r_idx + 1})")
                    add_btn.clicked.connect(lambda _, p=region.pipeline, r=root_index: self._show_node_picker(p, r))
                    region_layout.addWidget(add_btn)
                    
                    region_group.set_content_layout(region_layout)
                    layout.addWidget(region_group)
            else:
                layout.addWidget(QLabel("Регионы будут созданы автоматически\nпри рендере."))
            
        section.set_content_layout(layout)
        return section

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

    def _create_slider(self, layout, name: str, min_val: float, max_val: float, current: float, node_config, field_name: str, root_index: int):
        label = QLabel(f"{name}: {current:.2f}")
        layout.addWidget(label)
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(100)
        
        initial_pos = int(((current - min_val) / (max_val - min_val)) * 100)
        # Prevent division by zero if max_val == min_val
        if max_val == min_val: initial_pos = 0
        slider.setValue(initial_pos)
        layout.addWidget(slider)
        
        def on_change(val):
            real_val = min_val + (val / 100.0) * (max_val - min_val)
            label.setText(f"{name}: {real_val:.2f}")
            setattr(node_config, field_name, real_val)
            
            if field_name == "current_angle" and hasattr(node_config, "mode"):
                node_config.mode = "manual"
                
            self.controller._trigger_pipeline(start_node_index=root_index, is_interactive=True)
            
        def on_release():
            self.controller._trigger_pipeline(start_node_index=0, is_interactive=False)

        slider.valueChanged.connect(on_change)
        slider.sliderReleased.connect(on_release)

    def _on_checkbox_changed(self, node_config, field_name: str, state: int):
        setattr(node_config, field_name, state == Qt.Checked)
        self.controller._trigger_pipeline(start_node_index=0, is_interactive=False)
