from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent, QCursor
from tools.base_tool import BaseTool

class Eraser(BaseTool):
    def mousePressEvent(self, event: QMouseEvent, cell: QPoint):
        self.canvas.draw_pixel(cell.x(), cell.y(), self.app_state.secondary_color)

    def mouseMoveEvent(self, event: QMouseEvent, cell: QPoint):
        self.canvas.draw_pixel(cell.x(), cell.y(), self.app_state.secondary_color)

    def mouseReleaseEvent(self, event: QMouseEvent, cell: QPoint):
        pass

    def get_cursor(self) -> QCursor:
        return QCursor(Qt.CursorShape.PointingHandCursor)