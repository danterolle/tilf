from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent, QCursor
from tools.base_tool import BaseTool

class Fill(BaseTool):
    def mousePressEvent(self, event: QMouseEvent, cell: QPoint):
        self._flood_fill(cell.x(), cell.y(), self.app_state.primary_color)
        self.canvas.update()

    def mouseMoveEvent(self, event: QMouseEvent, cell: QPoint):
        pass

    def mouseReleaseEvent(self, event: QMouseEvent, cell: QPoint):
        pass

    def _flood_fill(self, start_col: int, start_row: int, new_color):
        target_rgba = self.canvas.image.pixel(start_col, start_row)
        new_rgba = new_color.rgba()
        if target_rgba == new_rgba:
            return

        stack = [(start_col, start_row)]
        while stack:
            col, row = stack.pop()
            if (0 <= col < self.canvas.columns
                    and 0 <= row < self.canvas.rows and self.canvas.image.pixel(col, row) == target_rgba):
                self.canvas.image.setPixel(col, row, new_rgba)
                stack.extend([(col + 1, row), (col - 1, row), (col, row + 1), (col, row - 1)])

    def get_cursor(self) -> QCursor:
        return QCursor(Qt.CursorShape.UpArrowCursor)