from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QCursor, QMouseEvent

from tools.base_tool import BaseTool


class Fill(BaseTool):
    def mousePressEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        changed = self.canvas.flood_fill(cell.x(), cell.y(), self.app_state.primary_color)
        if changed:
            self.canvas.update()
        return changed

    def mouseMoveEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        return False

    def mouseReleaseEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        return False

    def get_cursor(self) -> QCursor:
        return QCursor(Qt.CursorShape.UpArrowCursor)
