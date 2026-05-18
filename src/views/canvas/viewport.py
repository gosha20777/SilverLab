from PySide6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QToolBar, QMenu
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
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
        
        # Enable Drop for Diptych Swap
        self.view.setAcceptDrops(True)
        self.view.dragEnterEvent = self._on_drag_enter
        self.view.dragMoveEvent = self._on_drag_move
        self.view.dropEvent = self._on_drop
        
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
        
        # Event filter for ruler tool
        self.view.viewport().installEventFilter(self)
        self.ruler_line_item = None
        self.ruler_start = None

    def eventFilter(self, source, event) -> bool:
        from PySide6.QtCore import QEvent, Qt
        from PySide6.QtGui import QPen, QColor, QBrush
        import math
        
        if source == self.view.viewport() and getattr(self, 'current_tool', '') == 'picker':
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                scene_pos = self.view.mapToScene(event.pos())
                for item in self.scene.items():
                    if hasattr(item, 'pixmap'):
                        item_pos = item.mapFromScene(scene_pos)
                        ix, iy = int(item_pos.x()), int(item_pos.y())
                        pixmap = item.pixmap()
                        image = pixmap.toImage()
                        if 0 <= ix < image.width() and 0 <= iy < image.height():
                            color = image.pixelColor(ix, iy)
                            r, g, b = color.redF(), color.greenF(), color.blueF()
                            if hasattr(self.controller, 'apply_white_balance'):
                                self.controller.apply_white_balance(r, g, b)
                            self._activate_pan_tool()
                        break
                return True
                
        if source == self.view.viewport() and getattr(self, 'current_tool', '') == 'straighten':
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                scene_pos = self.view.mapToScene(event.pos())
                self.ruler_start = scene_pos
                pen = QPen(QColor(0, 255, 255), 3, Qt.SolidLine)
                self.ruler_line_item = self.scene.addLine(scene_pos.x(), scene_pos.y(), scene_pos.x(), scene_pos.y(), pen)
                self.ruler_p1 = self.scene.addEllipse(scene_pos.x() - 4, scene_pos.y() - 4, 8, 8, pen, QBrush(QColor(0, 255, 255)))
                self.ruler_p2 = self.scene.addEllipse(scene_pos.x() - 4, scene_pos.y() - 4, 8, 8, pen, QBrush(QColor(0, 255, 255)))
                return True
            elif event.type() == QEvent.MouseMove and getattr(self, 'ruler_line_item', None):
                scene_pos = self.view.mapToScene(event.pos())
                self.ruler_line_item.setLine(self.ruler_start.x(), self.ruler_start.y(), scene_pos.x(), scene_pos.y())
                self.ruler_p2.setRect(scene_pos.x() - 4, scene_pos.y() - 4, 8, 8)
                return True
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton and getattr(self, 'ruler_line_item', None):
                scene_pos = self.view.mapToScene(event.pos())
                dx = scene_pos.x() - self.ruler_start.x()
                dy = scene_pos.y() - self.ruler_start.y()
                
                self.scene.removeItem(self.ruler_line_item)
                self.scene.removeItem(self.ruler_p1)
                self.scene.removeItem(self.ruler_p2)
                self.ruler_line_item = None
                self.ruler_p1 = None
                self.ruler_p2 = None
                
                # Calculate angle in degrees
                if dx != 0 or dy != 0:
                    angle = math.degrees(math.atan2(dy, dx))
                    
                    # Normalize angle to -90..90
                    while angle > 90: angle -= 180
                    while angle < -90: angle += 180
                    
                    if angle > 45:
                        deviation = angle - 90 # Line is almost vertical (leaning right)
                    elif angle < -45:
                        deviation = angle + 90 # Line is almost vertical (leaning left)
                    else:
                        deviation = angle # Line is almost horizontal
                        
                    if hasattr(self.controller, 'apply_straighten_angle'):
                        self.controller.apply_straighten_angle(deviation)
                        
                    # Reset tool to pan
                    self._activate_pan_tool()
                return True
                
        return super().eventFilter(source, event)

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
        self.current_tool = 'pan'
        self._update_bbox_modes()
        if hasattr(self.controller, 'status_message_changed'):
            self.controller.status_message_changed.emit("Инструмент: Pan (Перетаскивание). ЛКМ для перемещения.")
            
    def _activate_crop_tool(self) -> None:
        self.view.setDragMode(QGraphicsView.NoDrag)
        self.current_tool = 'crop'
        self._update_bbox_modes()
        if hasattr(self.controller, 'status_message_changed'):
            self.controller.status_message_changed.emit("Инструмент: Crop (Обрезка).")

    def _activate_straighten_tool(self) -> None:
        self.view.setDragMode(QGraphicsView.NoDrag)
        self.current_tool = 'straighten'
        self._update_bbox_modes()
        if hasattr(self.controller, 'status_message_changed'):
            self.controller.status_message_changed.emit("Инструмент: Straighten. Проведите линию горизонта.")

    def _activate_picker_tool(self) -> None:
        self.view.setDragMode(QGraphicsView.NoDrag)
        self.current_tool = 'picker'
        self._update_bbox_modes()
        if hasattr(self.controller, 'status_message_changed'):
            self.controller.status_message_changed.emit("Инструмент: Picker. Кликните по области для баланса белого.")

    def _update_bbox_modes(self):
        from src.views.canvas.widgets import ResizableRectItem
        is_editable = (self.current_tool == 'crop')
        for item in self.scene.items():
            if isinstance(item, ResizableRectItem):
                item.set_edit_mode(is_editable)

    def render_container(self, container: FrameContainer) -> None:
        display_array = container.get_display_image(is_proxy=False)
        pixmap = numpy_to_qpixmap(display_array)
        
        self.scene.clear()
        pixmap_item = self.scene.addPixmap(pixmap)
        self.view.setSceneRect(pixmap_item.boundingRect())
        self._draw_bboxes(container, pixmap.width(), pixmap.height())

    def render_proxy(self, container: FrameContainer) -> None:
        display_array = container.get_display_image(is_proxy=True)
        pixmap = numpy_to_qpixmap(display_array)
        
        self.scene.clear()
        pixmap_item = self.scene.addPixmap(pixmap)
        
        # Calculate the exact scale factor between full-res and proxy
        scale = container.raw_image.shape[1] / container.raw_proxy.shape[1]
        pixmap_item.setScale(scale)
        
        # Set scene rect to the exact scaled image dimensions
        self.view.setSceneRect(pixmap_item.sceneBoundingRect())
            
        self._draw_bboxes(container, pixmap.width() * scale, pixmap.height() * scale)
        
    def _draw_bboxes(self, container: FrameContainer, w: float, h: float) -> None:
        from src.views.canvas.widgets import ResizableRectItem
        from PySide6.QtCore import QRectF
        
        is_editable = getattr(self, 'current_tool', 'pan') == 'crop'
        
        config = container.pipeline_config
        for node in config.nodes:
            if not node.enabled: continue
            
            if node.node_type == "SplitterNode":
                for idx, layout_rect in enumerate(getattr(node, 'layout_rects', [])):
                    nx, ny, nw, nh = layout_rect
                    rx, ry = nx * w, ny * h
                    rw, rh = nw * w, nh * h
                    
                    if rw > 0 and rh > 0:
                        rect_item = ResizableRectItem(idx, QRectF(0, 0, rw, rh))
                        rect_item.setPos(rx, ry)
                        rect_item.set_edit_mode(is_editable)
                        rect_item.setZValue(1)
                        rect_item.signals.rect_changed.connect(
                            lambda r_idx, new_rect, n=node, bw=w, bh=h: self._on_bbox_changed(r_idx, new_rect, n, bw, bh)
                        )
                        self.scene.addItem(rect_item)
                        
                # Final crop bbox
                fx, fy, fw, fh = getattr(node, 'final_crop', (0.0, 0.0, 1.0, 1.0))
                rx, ry = fx * w, fy * h
                rw, rh = fw * w, fh * h
                
                if rw > 0 and rh > 0:
                    rect_item = ResizableRectItem(-1, QRectF(0, 0, rw, rh))
                    rect_item.is_final_crop = True
                    rect_item.setPos(rx, ry)
                    rect_item.set_edit_mode(is_editable)
                    rect_item.setZValue(0) # Final crop is below regions
                    rect_item.signals.rect_changed.connect(
                        lambda r_idx, new_rect, n=node, bw=w, bh=h: self._on_bbox_changed(r_idx, new_rect, n, bw, bh)
                    )
                    self.scene.addItem(rect_item)
                    
            elif node.node_type == "CropNode":
                nx, ny, nw, nh = node.bbox
                rx, ry = nx * w, ny * h
                rw, rh = nw * w, nh * h
                
                if rw > 0 and rh > 0:
                    rect_item = ResizableRectItem(-2, QRectF(0, 0, rw, rh))
                    rect_item.aspect_ratio_str = getattr(node, "aspect_ratio", "free")
                    rect_item.grid_type = getattr(node, "grid_type", "none")
                    rect_item.setPos(rx, ry)
                    rect_item.set_edit_mode(is_editable)
                    rect_item.setZValue(2)
                    rect_item.signals.rect_changed.connect(
                        lambda r_idx, new_rect, n=node, bw=w, bh=h: self._on_bbox_changed(r_idx, new_rect, n, bw, bh)
                    )
                    self.scene.addItem(rect_item)
                        
    def _on_bbox_changed(self, region_index: int, new_rect, target_node, bw: float, bh: float) -> None:
        nx = new_rect.x() / bw
        ny = new_rect.y() / bh
        nw = new_rect.width() / bw
        nh = new_rect.height() / bh
        
        if region_index == -2:
            target_node.bbox = (nx, ny, nw, nh)
        elif region_index == -1:
            target_node.final_crop = (nx, ny, nw, nh)
            target_node.mode = "manual"
        elif region_index >= 0:
            if hasattr(target_node, 'layout_rects') and region_index < len(target_node.layout_rects):
                target_node.layout_rects[region_index] = (nx, ny, nw, nh)
            # Sync region.bbox only for native (non-swapped) regions
            if region_index < len(target_node.regions):
                region = target_node.regions[region_index]
                current_path = self.controller.sequence.active_container.file_path if self.controller.sequence.active_container else ""
                if region.source_file == current_path or not region.source_file:
                    region.bbox = (nx, ny, nw, nh)
            # Re-calculate final crop based on new layout_rects
            if hasattr(target_node, 'layout_rects') and len(target_node.layout_rects) == 2:
                r1 = target_node.layout_rects[0]
                r2 = target_node.layout_rects[1]
                top = min(r1[1], r2[1])
                bottom = max(r1[1] + r1[3], r2[1] + r2[3])
                left = min(r1[0], r2[0])
                right = max(r1[0] + r1[2], r2[0] + r2[2])
                
                # Apply 2% margins as in auto
                if top > 0.04: top = 0.02
                if bottom < 0.96: bottom = 0.98
                if left > 0.04: left = 0.02
                if right < 0.96: right = 0.98
                
                target_node.final_crop = (left, top, right - left, bottom - top)
            target_node.mode = "manual"
        
        self.controller.pipeline_changed.emit()
        self.controller._trigger_pipeline(start_node_index=0, is_interactive=False)

    # --- Drag & Drop for Diptych Swap ---

    def _on_drag_enter(self, event) -> None:
        """Accept drag events that carry file path data."""
        if event.mimeData().hasText() or event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def _on_drag_move(self, event) -> None:
        """Accept drag move to allow drop."""
        event.acceptProposedAction()

    def _on_drop(self, event) -> None:
        """Handle drop: determine which slot was targeted, show region picker."""
        # Extract file_path from mime data
        mime = event.mimeData()
        file_path = ""
        if mime.hasText():
            file_path = mime.text().strip()
        elif mime.hasUrls():
            urls = mime.urls()
            if urls:
                file_path = urls[0].toLocalFile()

        if not file_path:
            event.ignore()
            return

        # Convert mouse position to normalized canvas coordinates
        scene_pos = self.view.mapToScene(event.position().toPoint())
        scene_rect = self.view.sceneRect()
        if scene_rect.width() <= 0 or scene_rect.height() <= 0:
            event.ignore()
            return

        norm_x = scene_pos.x() / scene_rect.width()
        norm_y = scene_pos.y() / scene_rect.height()

        # Ask controller which slot is under the cursor
        slot_index = self.controller.get_diptych_slot_at_point(norm_x, norm_y)

        if slot_index >= 0:
            self._show_region_picker(file_path, slot_index)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _show_region_picker(self, source_file: str, target_slot: int) -> None:
        """Shows a popup menu to choose which region from source_file to swap in."""
        menu = QMenu(self)
        menu.addAction(
            "⬅ Левый регион (Left)",
            lambda: self.controller.swap_diptych_region(target_slot, source_file, 0),
        )
        menu.addAction(
            "➡ Правый регион (Right)",
            lambda: self.controller.swap_diptych_region(target_slot, source_file, 1),
        )
        menu.addSeparator()
        menu.addAction(
            "📄 Весь файл целиком",
            lambda: self.controller.swap_diptych_region(target_slot, source_file, -1),
        )
        menu.popup(QCursor.pos())
