from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame

class CollapsibleSection(QWidget):
    """
    A custom collapsible group box for the Inspector panel.
    """
    def __init__(self, title: str) -> None:
        super().__init__()
        self.is_collapsed = False
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toggle Button (Header)
        self.toggle_button = QPushButton(f"▼ {title}")
        self.toggle_button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                background-color: #3e3e3e;
                color: #ffffff;
                border: none;
                font-weight: bold;
                border-radius: 4px;
                margin-top: 5px;
            }
            QPushButton:hover { background-color: #4e4e4e; }
        """)
        self.toggle_button.clicked.connect(self.toggle)
        self.main_layout.addWidget(self.toggle_button)
        
        # Content Container
        self.content_widget = QFrame()
        self.content_widget.setStyleSheet("QFrame { background-color: #2b2b2b; }")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.addWidget(self.content_widget)

    def set_content_layout(self, layout) -> None:
        """Replaces the internal layout with the provided one or adds to it."""
        self.content_layout.addLayout(layout)

    def toggle(self) -> None:
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.toggle_button.setText(self.toggle_button.text().replace("▼", "▶"))
            self.content_widget.hide()
        else:
            self.toggle_button.setText(self.toggle_button.text().replace("▶", "▼"))
            self.content_widget.show()
