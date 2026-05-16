from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout
from src.core.isp.plugin_manager import plugin_manager

class NodePickerDialog(QDialog):
    """
    Dialog window allowing the user to select a new ISP node to append to the pipeline.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить фильтр (Add Node)")
        self.resize(300, 400)
        
        self.layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        
        self.available_nodes = []
        for node_type in plugin_manager.get_all_node_types():
            config_cls = plugin_manager.get_config_class(node_type)
            if config_cls:
                display_name = node_type
                if hasattr(config_cls, 'get_ui_schema'):
                    ui_schema = config_cls.get_ui_schema()
                    if ui_schema and len(ui_schema) > 0 and 'name' in ui_schema[0]:
                        display_name = f"{ui_schema[0]['name']} ({node_type})"
                self.available_nodes.append((display_name, config_cls))
                
        
        for name, _ in self.available_nodes:
            self.list_widget.addItem(name)
            
        self.layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.cancel_btn = QPushButton("Отмена")
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(btn_layout)
        
        self.add_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
    def get_selected_config(self):
        """
        Returns a new instance of the selected Pydantic node config.
        """
        idx = self.list_widget.currentRow()
        if idx >= 0:
            name, config_cls = self.available_nodes[idx]
            return config_cls()
        return None
