from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QListView
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
import numpy as np
import os
from src.controllers.main_controller import MainController
from src.utils.converters import numpy_to_qpixmap

class SequencePanel(QWidget):
    """
    Vertical gallery panel displaying thumbnails of the current image sequence.
    """
    def __init__(self, controller: MainController):
        super().__init__()
        self.controller = controller
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListView.IconMode)
        self.list_widget.setIconSize(QSize(180, 180))
        self.list_widget.setResizeMode(QListView.Adjust)
        self.list_widget.setSpacing(5)
        self.list_widget.setMovement(QListView.Static)
        self.list_widget.setWordWrap(True)
        self.list_widget.setStyleSheet(
            "QListWidget { background-color: #2b2b2b; border: none; } "
            "QListWidget::item { padding: 2px; }"
        )
        
        layout.addWidget(self.list_widget)
        
        self.items_map = {} # Maps file_path to QListWidgetItem
        
        self._connect_signals()
        
    def _connect_signals(self) -> None:
        self.controller.folder_loaded.connect(self._on_folder_loaded)
        self.controller.thumbnail_ready.connect(self._on_thumbnail_ready)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.controller.image_loaded.connect(self._on_image_loaded)
        
    def _on_folder_loaded(self) -> None:
        self.list_widget.clear()
        self.items_map.clear()
        
        for item_data in self.controller.sequence.items:
            path = item_data.file_path
            list_item = QListWidgetItem(os.path.basename(path))
            list_item.setData(Qt.UserRole, path)
            list_item.setTextAlignment(Qt.AlignCenter)
            # Force Qt to reserve space for the icon before it asynchronously loads
            # We use a 180x180 square as a placeholder. It will be dynamically resized later.
            list_item.setSizeHint(QSize(180, 180)) 
            self.list_widget.addItem(list_item)
            self.items_map[path] = list_item
            
    def _on_thumbnail_ready(self, file_path: str, thumbnail_data: np.ndarray) -> None:
        if file_path in self.items_map:
            list_item = self.items_map[file_path]
            pixmap = numpy_to_qpixmap(thumbnail_data)
            list_item.setIcon(QIcon(pixmap))
            
            # Dynamically calculate the item's height based on the image's aspect ratio
            h, w = thumbnail_data.shape[:2]
            
            # Qt scales the icon to fit within the 180x180 box
            scale = 180 / max(h, w)
            scaled_h = int(h * scale)
            
            # Reserve 180px width for text wrapping, and scaled_h + 30px for the text height
            list_item.setSizeHint(QSize(180, scaled_h + 30))
            
    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        file_path = item.data(Qt.UserRole)
        if file_path:
            self.controller.load_image(file_path)
            
    def _on_image_loaded(self, container) -> None:
        """ Highlights the currently active image in the sequence list """
        path = container.file_path
        if path in self.items_map:
            item = self.items_map[path]
            self.list_widget.setCurrentItem(item)
