from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent, QColor

from state import AppState
from tools.base_tool import BaseTool
from ui.canvas import Canvas


class Pencil(BaseTool):
    def __init__(self, canvas: Canvas, app_state: AppState):
        super().__init__(canvas, app_state)
        self._draw_color: QColor = self.app_state.primary_color

    def mousePressEvent(self, event: QMouseEvent, cell: QPoint):
        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            self._draw_color = self.app_state.secondary_color
        else:
            self._draw_color = self.app_state.primary_color
        self.canvas.draw_pixel(cell.x(), cell.y(), self._draw_color)

    def mouseMoveEvent(self, event: QMouseEvent, cell: QPoint):
        self.canvas.draw_pixel(cell.x(), cell.y(), self._draw_color)

    def mouseReleaseEvent(self, event: QMouseEvent, cell: QPoint):
        # Reset draw color for the next stroke
        self._draw_color = self.app_state.primary_color