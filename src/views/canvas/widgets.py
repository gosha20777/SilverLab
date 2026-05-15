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
        
    def hoverMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self.resizing:
            return super().hoverMoveEvent(event)
            
        pos = event.pos()
        rect = self.rect()
        
        # Check corners first
        hs = self.handle_size
        if pos.x() < rect.left() + hs and pos.y() < rect.top() + hs:
            self.setCursor(Qt.SizeFDiagCursor)
        elif pos.x() > rect.right() - hs and pos.y() > rect.bottom() - hs:
            self.setCursor(Qt.SizeFDiagCursor)
        elif pos.x() > rect.right() - hs and pos.y() < rect.top() + hs:
            self.setCursor(Qt.SizeBDiagCursor)
        elif pos.x() < rect.left() + hs and pos.y() > rect.bottom() - hs:
            self.setCursor(Qt.SizeBDiagCursor)
        # Then edges
        elif pos.x() < rect.left() + hs:
            self.setCursor(Qt.SizeHorCursor)
        elif pos.x() > rect.right() - hs:
            self.setCursor(Qt.SizeHorCursor)
        elif pos.y() < rect.top() + hs:
            self.setCursor(Qt.SizeVerCursor)
        elif pos.y() > rect.bottom() - hs:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.SizeAllCursor)
            
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)
        
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            rect = self.rect()
            hs = self.handle_size
            
            # Determine resize direction
            if pos.x() < rect.left() + hs and pos.y() < rect.top() + hs:
                self.resize_dir = 'tl'
            elif pos.x() > rect.right() - hs and pos.y() > rect.bottom() - hs:
                self.resize_dir = 'br'
            elif pos.x() > rect.right() - hs and pos.y() < rect.top() + hs:
                self.resize_dir = 'tr'
            elif pos.x() < rect.left() + hs and pos.y() > rect.bottom() - hs:
                self.resize_dir = 'bl'
            elif pos.x() < rect.left() + hs:
                self.resize_dir = 'l'
            elif pos.x() > rect.right() - hs:
                self.resize_dir = 'r'
            elif pos.y() < rect.top() + hs:
                self.resize_dir = 't'
            elif pos.y() > rect.bottom() - hs:
                self.resize_dir = 'b'
            else:
                self.resize_dir = None
                
            if self.resize_dir:
                self.resizing = True
                self.setFlag(QGraphicsItem.ItemIsMovable, False)
                
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
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
                
            self.setRect(rect.normalized())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
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
