from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsSceneMouseEvent
from PySide6.QtGui import QPen, QBrush, QColor, QCursor
from PySide6.QtCore import Qt, QRectF, Signal, QObject

class RectSignals(QObject):
    rect_changed = Signal(int, QRectF) # region_index, new_rect

class ResizableRectItem(QGraphicsRectItem):
    """
    A Graphics Rect Item that can be resized and moved.
    Used for interactive BBox control on the Canvas.
    """
    handle_size = 12.0

    def __init__(self, region_index: int, rect: QRectF, parent=None):
        super().__init__(rect, parent)
        self.region_index = region_index
        self.signals = RectSignals()
        
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        self.setPen(QPen(QColor(0, 255, 0, 200), 2, Qt.DashLine))
        self.setBrush(QBrush(QColor(0, 255, 0, 30)))
        
        self.resizing = False
        self.resize_dir = None # 'tl', 'tr', 'bl', 'br', 'l', 'r', 't', 'b'
        self.is_final_crop = False
        self.is_editable = False
        
        self.aspect_ratio_str = "free"
        self.grid_type = "none"
        
    def set_edit_mode(self, editable: bool):
        self.is_editable = editable
        if self.is_final_crop:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            self.setAcceptHoverEvents(False)
        else:
            self.setFlag(QGraphicsItem.ItemIsMovable, editable)
            self.setAcceptHoverEvents(editable)
            
        if editable:
            if self.is_final_crop:
                self.setPen(QPen(QColor(0, 150, 255, 200), 2, Qt.DashLine))
                self.setBrush(QBrush(QColor(0, 150, 255, 30)))
            else:
                self.setPen(QPen(QColor(0, 255, 0, 200), 2, Qt.DashLine))
                self.setBrush(QBrush(QColor(0, 255, 0, 30)))
        else:
            if self.is_final_crop:
                self.setPen(QPen(QColor(0, 150, 255, 150), 2, Qt.DashLine))
                self.setBrush(QBrush(Qt.transparent))
            else:
                self.setPen(QPen(QColor(0, 255, 0, 150), 2, Qt.DashLine))
                self.setBrush(QBrush(Qt.transparent))
                
    def hoverMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if not self.is_editable or self.is_final_crop:
            event.ignore()
            return
            
        if self.resizing:
            return super().hoverMoveEvent(event)
            
        pos = event.pos()
        rect = self.rect()
        
        # Dynamic handle size based on rect dimensions to fix scaling issues
        hs_x = max(10.0, rect.width() * 0.05)
        hs_y = max(10.0, rect.height() * 0.05)
        
        # Check corners first
        if pos.x() < rect.left() + hs_x and pos.y() < rect.top() + hs_y:
            self.setCursor(Qt.SizeFDiagCursor)
        elif pos.x() > rect.right() - hs_x and pos.y() > rect.bottom() - hs_y:
            self.setCursor(Qt.SizeFDiagCursor)
        elif pos.x() > rect.right() - hs_x and pos.y() < rect.top() + hs_y:
            self.setCursor(Qt.SizeBDiagCursor)
        elif pos.x() < rect.left() + hs_x and pos.y() > rect.bottom() - hs_y:
            self.setCursor(Qt.SizeBDiagCursor)
        # Then edges
        elif pos.x() < rect.left() + hs_x:
            self.setCursor(Qt.SizeHorCursor)
        elif pos.x() > rect.right() - hs_x:
            self.setCursor(Qt.SizeHorCursor)
        elif pos.y() < rect.top() + hs_y:
            self.setCursor(Qt.SizeVerCursor)
        elif pos.y() > rect.bottom() - hs_y:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.SizeAllCursor)
            
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)
        
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if not self.is_editable or self.is_final_crop:
            event.ignore()
            return
            
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            rect = self.rect()
            
            hs_x = max(10.0, rect.width() * 0.05)
            hs_y = max(10.0, rect.height() * 0.05)
            
            # Determine resize direction
            if pos.x() < rect.left() + hs_x and pos.y() < rect.top() + hs_y:
                self.resize_dir = 'tl'
            elif pos.x() > rect.right() - hs_x and pos.y() > rect.bottom() - hs_y:
                self.resize_dir = 'br'
            elif pos.x() > rect.right() - hs_x and pos.y() < rect.top() + hs_y:
                self.resize_dir = 'tr'
            elif pos.x() < rect.left() + hs_x and pos.y() > rect.bottom() - hs_y:
                self.resize_dir = 'bl'
            elif pos.x() < rect.left() + hs_x:
                self.resize_dir = 'l'
            elif pos.x() > rect.right() - hs_x:
                self.resize_dir = 'r'
            elif pos.y() < rect.top() + hs_y:
                self.resize_dir = 't'
            elif pos.y() > rect.bottom() - hs_y:
                self.resize_dir = 'b'
            else:
                self.resize_dir = None
                
            if self.resize_dir:
                self.resizing = True
                self.setFlag(QGraphicsItem.ItemIsMovable, False)
                
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if not self.is_editable or self.is_final_crop:
            event.ignore()
            return
            
        if self.resizing:
            pos = event.pos()
            rect = self.rect()
            
            if self.resize_dir == 'tl':
                rect.setTopLeft(pos)
            elif self.resize_dir == 'tr':
                rect.setTopRight(pos)
            elif self.resize_dir == 'bl':
                rect.setBottomLeft(pos)
            elif self.resize_dir == 'br':
                rect.setBottomRight(pos)
            elif self.resize_dir == 'l':
                rect.setLeft(pos.x())
            elif self.resize_dir == 'r':
                rect.setRight(pos.x())
            elif self.resize_dir == 't':
                rect.setTop(pos.y())
            elif self.resize_dir == 'b':
                rect.setBottom(pos.y())
                
            if self.aspect_ratio_str and self.aspect_ratio_str != "free":
                w_r, h_r = map(float, self.aspect_ratio_str.split(':'))
                target_ratio = w_r / h_r
                
                # We enforce aspect ratio by adjusting the opposite dimension
                new_w, new_h = rect.width(), rect.height()
                
                if self.resize_dir in ('l', 'r', 'tl', 'tr', 'bl', 'br'):
                    # Width drives height
                    new_h = new_w / target_ratio
                else:
                    # Height drives width
                    new_w = new_h * target_ratio
                    
                if self.resize_dir == 'tl':
                    rect.setTop(rect.bottom() - new_h)
                elif self.resize_dir == 'tr':
                    rect.setTop(rect.bottom() - new_h)
                elif self.resize_dir == 'bl':
                    rect.setBottom(rect.top() + new_h)
                elif self.resize_dir == 'br':
                    rect.setBottom(rect.top() + new_h)
                elif self.resize_dir == 'l':
                    rect.setTop(rect.center().y() - new_h/2)
                    rect.setBottom(rect.center().y() + new_h/2)
                elif self.resize_dir == 'r':
                    rect.setTop(rect.center().y() - new_h/2)
                    rect.setBottom(rect.center().y() + new_h/2)
                elif self.resize_dir == 't':
                    rect.setLeft(rect.center().x() - new_w/2)
                    rect.setRight(rect.center().x() + new_w/2)
                elif self.resize_dir == 'b':
                    rect.setLeft(rect.center().x() - new_w/2)
                    rect.setRight(rect.center().x() + new_w/2)
                
            self.setRect(rect.normalized())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if not self.is_editable or self.is_final_crop:
            event.ignore()
            return
            
        if self.resizing:
            self.resizing = False
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            self._emit_rect_changed()
        else:
            super().mouseReleaseEvent(event)
            self._emit_rect_changed()
            
    def _emit_rect_changed(self):
        # Calculate world coordinates
        mapped_rect = self.mapRectToScene(self.rect())
        self.signals.rect_changed.emit(self.region_index, mapped_rect)

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.resizing and getattr(self, 'grid_type', 'none') != 'none':
            rect = self.rect()
            painter.setPen(QPen(QColor(255, 255, 255, 200), max(1.0, rect.width() * 0.002), Qt.DashLine))
            
            if self.grid_type == "rule_of_thirds":
                x1, x2 = rect.left() + rect.width()/3, rect.left() + 2*rect.width()/3
                y1, y2 = rect.top() + rect.height()/3, rect.top() + 2*rect.height()/3
                painter.drawLine(x1, rect.top(), x1, rect.bottom())
                painter.drawLine(x2, rect.top(), x2, rect.bottom())
                painter.drawLine(rect.left(), y1, rect.right(), y1)
                painter.drawLine(rect.left(), y2, rect.right(), y2)
                
            elif self.grid_type == "golden_ratio":
                x1, x2 = rect.left() + rect.width()*0.382, rect.left() + rect.width()*0.618
                y1, y2 = rect.top() + rect.height()*0.382, rect.top() + rect.height()*0.618
                painter.drawLine(x1, rect.top(), x1, rect.bottom())
                painter.drawLine(x2, rect.top(), x2, rect.bottom())
                painter.drawLine(rect.left(), y1, rect.right(), y1)
                painter.drawLine(rect.left(), y2, rect.right(), y2)
