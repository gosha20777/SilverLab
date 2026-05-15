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
        self.controller.proxy_processed.connect(self.render_proxy)
        
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
        display_array = container.get_display_image(is_proxy=False)
        pixmap = numpy_to_qpixmap(display_array)
        
        self.scene.clear()
        pixmap_item = self.scene.addPixmap(pixmap)
        self.view.setSceneRect(self.scene.itemsBoundingRect())
        self._draw_bboxes(container, pixmap.width(), pixmap.height())

    def render_proxy(self, container: FrameContainer) -> None:
        display_array = container.get_display_image(is_proxy=True)
        pixmap = numpy_to_qpixmap(display_array)
        
        rect = self.scene.itemsBoundingRect() if self.scene.items() else None
        
        self.scene.clear()
        pixmap_item = self.scene.addPixmap(pixmap)
        
        scale = 1.0
        if rect and not rect.isEmpty():
            scale_x = rect.width() / pixmap.width()
            scale_y = rect.height() / pixmap.height()
            scale = max(scale_x, scale_y)
            pixmap_item.setScale(scale)
            self.view.setSceneRect(rect)
        else:
            self.view.setSceneRect(self.scene.itemsBoundingRect())
            
        self._draw_bboxes(container, pixmap.width() * scale, pixmap.height() * scale)
        
    def _draw_bboxes(self, container: FrameContainer, w: float, h: float) -> None:
        from src.views.canvas.widgets import ResizableRectItem
        from PySide6.QtCore import QRectF
        
        config = container.pipeline_config
        for node in config.nodes:
            if node.node_type == "SplitterNode" and node.enabled:
                for idx, region in enumerate(node.regions):
                    nx, ny, nw, nh = region.bbox
                    rx, ry = nx * w, ny * h
                    rw, rh = nw * w, nh * h
                    
                    if rw > 0 and rh > 0:
                        rect_item = ResizableRectItem(idx, QRectF(0, 0, rw, rh))
                        rect_item.setPos(rx, ry)
                        rect_item.signals.rect_changed.connect(
                            lambda r_idx, new_rect, n=node, bw=w, bh=h: self._on_bbox_changed(r_idx, new_rect, n, bw, bh)
                        )
                        self.scene.addItem(rect_item)
                        
    def _on_bbox_changed(self, region_index: int, new_rect, splitter_node, bw: float, bh: float) -> None:
        # new_rect is in scene coordinates (pixels)
        # Convert back to normalized coordinates
        nx = new_rect.x() / bw
        ny = new_rect.y() / bh
        nw = new_rect.width() / bw
        nh = new_rect.height() / bh
        
        splitter_node.regions[region_index].bbox = (nx, ny, nw, nh)
        splitter_node.mode = "manual"
        
        self.controller.pipeline_changed.emit()
        self.controller._trigger_pipeline(start_node_index=0, is_interactive=False)
