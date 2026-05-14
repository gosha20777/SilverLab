from PySide6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QToolBar
from PySide6.QtCore import Qt
from src.controllers.main_controller import MainController
from src.models.frame_container import FrameContainer
from src.utils.converters import numpy_to_qpixmap

class CanvasViewport(QWidget):
    """
    Widget containing the Main Canvas (QGraphicsView) and its Toolbar.
    Manages the 'Tool State' (Pan, Crop, Straighten).
    """
    def __init__(self, controller: MainController) -> None:
        super().__init__()
        self.controller = controller
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Toolbar
        self.toolbar = QToolBar("Canvas Tools")
        self.toolbar.setOrientation(Qt.Horizontal)
        self.toolbar.setStyleSheet("QToolBar { background-color: #3e3e3e; border: none; padding: 4px; }")
        
        self.action_pan = self.toolbar.addAction("✋ Pan")
        self.action_crop = self.toolbar.addAction("✂️ Crop")
        self.action_straighten = self.toolbar.addAction("📏 Straighten")
        self.action_picker = self.toolbar.addAction("💉 Picker")
        
        self.layout.addWidget(self.toolbar)
        
        # Graphics View & Scene
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("background-color: #1e1e1e; border: none;")
        self.view.setDragMode(QGraphicsView.ScrollHandDrag) # Default to Pan tool
        self.view.wheelEvent = self._on_canvas_wheel_event
        
        self.layout.addWidget(self.view)
        
        self._connect_signals()
        
    def _on_canvas_wheel_event(self, event) -> None:
        """
        Zoom with mouse wheel.
        """
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            
        self.view.scale(zoom_factor, zoom_factor)
        
    def _connect_signals(self) -> None:
        self.controller.image_loaded.connect(self.render_container)
        self.controller.image_processed.connect(self.render_container)
        
        # Tool actions
        self.action_pan.triggered.connect(self._activate_pan_tool)
        self.action_crop.triggered.connect(self._activate_crop_tool)
        self.action_straighten.triggered.connect(self._activate_straighten_tool)
        self.action_picker.triggered.connect(self._activate_picker_tool)
        
    def _activate_pan_tool(self) -> None:
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        if hasattr(self.controller, 'status_message_changed'):
            self.controller.status_message_changed.emit("Инструмент: Pan (Перетаскивание). ЛКМ для перемещения.")
            
    def _activate_crop_tool(self) -> None:
        self.view.setDragMode(QGraphicsView.NoDrag)
        if hasattr(self.controller, 'status_message_changed'):
            self.controller.status_message_changed.emit("Инструмент: Crop (Обрезка).")

    def _activate_straighten_tool(self) -> None:
        self.view.setDragMode(QGraphicsView.NoDrag)
        if hasattr(self.controller, 'status_message_changed'):
            self.controller.status_message_changed.emit("Инструмент: Straighten. Проведите линию горизонта.")

    def _activate_picker_tool(self) -> None:
        self.view.setDragMode(QGraphicsView.NoDrag)
        if hasattr(self.controller, 'status_message_changed'):
            self.controller.status_message_changed.emit("Инструмент: Picker. Кликните по области для баланса белого.")

    def render_container(self, container: FrameContainer) -> None:
        display_array = container.get_display_image()
        pixmap = numpy_to_qpixmap(display_array)
        
        self.scene.clear()
        self.scene.addPixmap(pixmap)
        self.view.setSceneRect(self.scene.itemsBoundingRect())
