from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QCheckBox
from PySide6.QtCore import Signal

class CollapsibleSection(QWidget):
    """
    A custom collapsible group box for the Inspector panel.
    Now includes a checkbox, up/down/delete controls.
    """
    
    # Signals for pipeline management
    move_up_requested = Signal()
    move_down_requested = Signal()
    delete_requested = Signal()
    enabled_changed = Signal(bool)
    
    def __init__(self, title: str, start_collapsed: bool = False) -> None:
        super().__init__()
        self.is_collapsed = start_collapsed
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 4)
        
        # Header Container
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(4, 4, 4, 4)
        self.header_layout.setSpacing(4)
        self.header_widget.setStyleSheet("background-color: #3e3e3e; border-radius: 4px;")
        
        # Checkbox
        self.enable_checkbox = QCheckBox()
        self.enable_checkbox.setChecked(True)
        self.enable_checkbox.toggled.connect(self.enabled_changed.emit)
        self.header_layout.addWidget(self.enable_checkbox)
        
        # Toggle Button
        self.toggle_button = QPushButton(f"{'▶' if start_collapsed else '▼'} {title}")
        self.toggle_button.setStyleSheet("""
            QPushButton {
                text-align: left;
                background-color: transparent;
                color: #ffffff;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover { color: #aaaaaa; }
        """)
        self.toggle_button.clicked.connect(self.toggle)
        self.header_layout.addWidget(self.toggle_button, stretch=1)
        
        # Controls
        self.up_button = QPushButton("↑")
        self.up_button.setFixedSize(24, 24)
        self.up_button.clicked.connect(self.move_up_requested.emit)
        self.header_layout.addWidget(self.up_button)
        
        self.down_button = QPushButton("↓")
        self.down_button.setFixedSize(24, 24)
        self.down_button.clicked.connect(self.move_down_requested.emit)
        self.header_layout.addWidget(self.down_button)
        
        self.delete_button = QPushButton("✕")
        self.delete_button.setFixedSize(24, 24)
        self.delete_button.setStyleSheet("color: #ff5555; font-weight: bold;")
        self.delete_button.clicked.connect(self.delete_requested.emit)
        self.header_layout.addWidget(self.delete_button)
        
        self.main_layout.addWidget(self.header_widget)
        
        # Content Container
        self.content_widget = QFrame()
        self.content_widget.setStyleSheet("QFrame { background-color: #2b2b2b; }")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.addWidget(self.content_widget)
        
        if start_collapsed:
            self.content_widget.hide()

    def set_content_layout(self, layout) -> None:
        """Replaces the internal layout with the provided one or adds to it."""
        self.content_layout.addLayout(layout)

    def set_enabled_state(self, state: bool) -> None:
        """Sets the checkbox state without emitting signals."""
        self.enable_checkbox.blockSignals(True)
        self.enable_checkbox.setChecked(state)
        self.enable_checkbox.blockSignals(False)
        self.content_widget.setEnabled(state)

    def toggle(self) -> None:
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.toggle_button.setText(self.toggle_button.text().replace("▼", "▶"))
            self.content_widget.hide()
        else:
            self.toggle_button.setText(self.toggle_button.text().replace("▶", "▼"))
            self.content_widget.show()
