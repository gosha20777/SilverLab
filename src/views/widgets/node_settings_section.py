from PySide6.QtWidgets import QVBoxLayout, QLabel, QSlider, QCheckBox, QPushButton
from PySide6.QtCore import Qt
from src.models.isp.enums import UIType
from src.views.widgets.collapsible import CollapsibleSection

class NodeSettingsSection(CollapsibleSection):
    """
    A specific CollapsibleSection that renders the UI schema for an ISP node.
    """
    def __init__(self, node_config, parent_pipeline, local_index: int, root_index: int, inspector) -> None:
        info = node_config.get_node_info()
        super().__init__(info.title, start_collapsed=False)
        
        self.node_config = node_config
        self.parent_pipeline = parent_pipeline
        self.local_index = local_index
        self.root_index = root_index
        self.inspector = inspector
        self.controller = inspector.controller
        
        self.set_enabled_state(self.node_config.enabled)
        
        layout = QVBoxLayout()
        self._build_ui(layout)
        self.set_content_layout(layout)
        
        self._connect_signals()

    def _connect_signals(self):
        def on_toggle(state):
            self.node_config.enabled = state
            self.controller._trigger_pipeline(start_node_index=self.root_index, is_interactive=False)
            
        def on_delete():
            self.parent_pipeline.nodes.pop(self.local_index)
            self.controller.pipeline_changed.emit()
            self.controller._trigger_pipeline(start_node_index=self.root_index, is_interactive=False)
            
        def on_move(direction):
            new_idx = self.local_index + direction
            if 0 <= new_idx < len(self.parent_pipeline.nodes):
                nodes = self.parent_pipeline.nodes
                nodes[self.local_index], nodes[new_idx] = nodes[new_idx], nodes[self.local_index]
                self.controller.pipeline_changed.emit()
                self.controller._trigger_pipeline(start_node_index=self.root_index if self.root_index <= new_idx else new_idx, is_interactive=False)

        self.enabled_changed.connect(on_toggle)
        self.move_up_requested.connect(lambda: on_move(-1))
        self.move_down_requested.connect(lambda: on_move(1))
        self.delete_requested.connect(on_delete)

    def _build_ui(self, layout):
        ui_schema = []
        if hasattr(self.node_config, "get_ui_schema"):
            ui_schema = self.node_config.get_ui_schema()
            
        for element in ui_schema:
            if element.type == UIType.SLIDER:
                self._create_slider(layout, element)
            elif element.type == UIType.CHECKBOX:
                self._create_checkbox(layout, element)
            elif element.type == UIType.LABEL:
                layout.addWidget(QLabel(element.text))
            elif element.type == UIType.CUSTOM and element.renderer == "splitter_regions":
                self._render_splitter_regions(layout)

    def _create_slider(self, layout, element):
        name = element.name
        min_val = element.min
        max_val = element.max
        field_name = element.field
        current = getattr(self.node_config, field_name)
        
        label = QLabel(f"{name}: {current:.2f}")
        layout.addWidget(label)
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(100)
        
        initial_pos = int(((current - min_val) / (max_val - min_val)) * 100)
        if max_val == min_val: initial_pos = 0
        slider.setValue(initial_pos)
        layout.addWidget(slider)
        
        def on_change(val):
            real_val = min_val + (val / 100.0) * (max_val - min_val)
            label.setText(f"{name}: {real_val:.2f}")
            setattr(self.node_config, field_name, real_val)
            
            if field_name == "current_angle" and hasattr(self.node_config, "mode"):
                self.node_config.mode = "manual"
                
            self.controller._trigger_pipeline(start_node_index=self.root_index, is_interactive=True)
            
        def on_release():
            self.controller._trigger_pipeline(start_node_index=0, is_interactive=False)

        slider.valueChanged.connect(on_change)
        slider.sliderReleased.connect(on_release)

    def _create_checkbox(self, layout, element):
        cb = QCheckBox(element.name)
        cb.setChecked(getattr(self.node_config, element.field))
        
        def on_checkbox_changed(state):
            setattr(self.node_config, element.field, state == Qt.Checked)
            self.controller._trigger_pipeline(start_node_index=0, is_interactive=False)
            
        cb.stateChanged.connect(on_checkbox_changed)
        layout.addWidget(cb)

    def _render_splitter_regions(self, layout):
        from PySide6.QtWidgets import QWidget
        self.regions_container = QWidget()
        self.regions_layout = QVBoxLayout(self.regions_container)
        self.regions_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.regions_container)
        
        self._rendered_regions_count = -1
        self._rebuild_regions()
        
        # Subscribe to image_processed signal to rebuild if regions changed
        self.inspector.controller.image_processed.connect(self._check_regions_update)

    def _check_regions_update(self, container):
        if hasattr(self.node_config, "regions"):
            if len(self.node_config.regions) != self._rendered_regions_count:
                self._rebuild_regions()

    def _rebuild_regions(self):
        # clear regions_layout
        while self.regions_layout.count():
            item = self.regions_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        self._rendered_regions_count = len(self.node_config.regions) if hasattr(self.node_config, "regions") else 0
        
        if self.node_config.regions:
            for r_idx, region in enumerate(self.node_config.regions):
                region_group = CollapsibleSection(f"Регион {r_idx + 1}", start_collapsed=True)
                region_group.set_enabled_state(getattr(region, "enabled", True))
                
                def on_region_toggle(state, r=region):
                    r.enabled = state
                    self.controller._trigger_pipeline(start_node_index=self.root_index, is_interactive=False)
                    
                region_group.enabled_changed.connect(on_region_toggle)
                
                region_layout = QVBoxLayout()
                
                # Recursive render
                self.inspector._render_node_list(region_layout, region.pipeline, is_root=False, root_index=self.root_index)
                
                # Add node button for this region
                add_btn = QPushButton(f"+ Добавить фильтр (Регион {r_idx + 1})")
                add_btn.clicked.connect(lambda _, p=region.pipeline, r=self.root_index: self.inspector._show_node_picker(p, r))
                region_layout.addWidget(add_btn)
                
                region_group.set_content_layout(region_layout)
                self.regions_layout.addWidget(region_group)
        else:
            self.regions_layout.addWidget(QLabel("Регионы будут созданы автоматически\\nпри рендере."))
