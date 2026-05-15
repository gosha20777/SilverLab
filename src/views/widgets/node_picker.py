from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout
from src.models.isp_config import (
    ExposureConfig, BlackClipConfig, WhitePatchConfig, 
    ContrastStretchConfig, AdaptiveGammaConfig, VibranceConfig,
    RotationConfig, SplitterConfig
)

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
        
        self.available_nodes = [
            ("Экспозиция (Exposure)", ExposureConfig),
            ("Отсечение черного (Black Clip)", BlackClipConfig),
            ("Баланс Белого (White Patch)", WhitePatchConfig),
            ("Контраст (Linear Stretch)", ContrastStretchConfig),
            ("Средние тона (Adaptive Gamma)", AdaptiveGammaConfig),
            ("Насыщенность (Vibrance)", VibranceConfig),
            ("Поворот (Rotation)", RotationConfig),
            ("Диптих (Splitter)", SplitterConfig)
        ]
        
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
