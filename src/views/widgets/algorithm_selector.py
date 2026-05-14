from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QStackedWidget

class AlgorithmSelector(QWidget):
    """
    Widget that combines a ComboBox with a StackedWidget.
    Selecting an algorithm in the ComboBox displays its corresponding control panel.
    """
    def __init__(self) -> None:
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.combo_box = QComboBox()
        self.layout.addWidget(self.combo_box)
        
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)
        
        self.combo_box.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)
        
    def add_algorithm(self, name: str, config_widget: QWidget) -> None:
        """
        Adds an algorithm to the selector.
        
        Args:
            name (str): The display name in the combobox.
            config_widget (QWidget): The UI controls for this specific algorithm.
        """
        self.combo_box.addItem(name)
        self.stacked_widget.addWidget(config_widget)
