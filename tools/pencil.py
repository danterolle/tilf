from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QMouseEvent

from state import AppState
from tools.base_tool import BaseTool

if TYPE_CHECKING:
    from ui.canvas import Canvas


class Pencil(BaseTool):
    is_drag_tool = True

    def __init__(self, canvas: Canvas, app_state: AppState) -> None:
        super().__init__(canvas, app_state)
        self._draw_color: QColor = self.app_state.primary_color

    def mousePressEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            self._draw_color = self.app_state.secondary_color
        else:
            self._draw_color = self.app_state.primary_color
        return self.canvas.draw_pixel(cell.x(), cell.y(), self._draw_color)

    def mouseMoveEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        return self.canvas.draw_pixel(cell.x(), cell.y(), self._draw_color)

    def mouseReleaseEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        self._draw_color = self.app_state.primary_color
        return False
