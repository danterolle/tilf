from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QCursor, QMouseEvent

from tools.base_tool import BaseTool


class Eraser(BaseTool):
    is_drag_tool = True

    def mousePressEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        return self.canvas.draw_pixel(cell.x(), cell.y(), self.app_state.secondary_color)

    def mouseMoveEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        return self.canvas.draw_pixel(cell.x(), cell.y(), self.app_state.secondary_color)

    def mouseReleaseEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        return False

    def get_cursor(self) -> QCursor:
        return QCursor(Qt.CursorShape.PointingHandCursor)
