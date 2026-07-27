from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QImage, QMouseEvent, QPainter, QPen

from state import AppState
from tools.base_tool import BaseTool

if TYPE_CHECKING:
    from ui.canvas import Canvas


class Shape(BaseTool):
    is_drag_tool = True

    def __init__(self, canvas: Canvas, app_state: AppState) -> None:
        super().__init__(canvas, app_state)
        self._shape_start_pos: QPoint | None = None
        self._shape_end_pos: QPoint | None = None
        self._preview_image: QImage | None = None

    def mousePressEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        self._shape_start_pos = cell
        self._preview_image = QImage(self.canvas.image.size(), QImage.Format.Format_ARGB32)
        self._preview_image.fill(Qt.GlobalColor.transparent)
        return False

    def mouseMoveEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        if self._preview_image is None:
            return False

        self._shape_end_pos = cell
        self._draw_shape_preview(bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier))
        return False

    def mouseReleaseEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        if self._shape_start_pos is None:
            return False

        self._shape_end_pos = cell
        changed = self._draw_shape_to_canvas(bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier))
        self._preview_image = None
        self._shape_start_pos = None
        self._shape_end_pos = None
        self.canvas.update()
        return changed

    def paint(self, painter: QPainter) -> None:
        if self._preview_image is not None:
            target_rect = QRect(
                0,
                0,
                self.canvas.columns * self.canvas.cell_size,
                self.canvas.rows * self.canvas.cell_size
            )
            painter.drawImage(target_rect, self._preview_image)

    def _get_shape_rect(self, force_square: bool) -> QRect:
        if self._shape_start_pos is None or self._shape_end_pos is None:
            return QRect()

        x1, y1 = self._shape_start_pos.x(), self._shape_start_pos.y()
        x2, y2 = self._shape_end_pos.x(), self._shape_end_pos.y()

        if force_square:
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            size = max(dx, dy)
            x2 = x1 + size if x2 >= x1 else x1 - size
            y2 = y1 + size if y2 >= y1 else y1 - size

        # Normalize the rectangle's coordinates. This ensures we have the correct
        # top-left (min x, min y) and bottom-right (max x, max y) points,
        # regardless of the direction the user dragged the mouse.
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)

        # Clamping the final rectangle coordinates to the canvas boundaries
        # to prevent any out-of-bounds drawing.
        left = max(0, left)
        top = max(0, top)
        right = min(self.canvas.columns - 1, right)
        bottom = min(self.canvas.rows - 1, bottom)

        width = right - left + 1
        height = bottom - top + 1

        return QRect(left, top, width, height)

    def _draw_shape_preview(self, force_square: bool) -> None:
        if self._preview_image is None:
            return

        self._preview_image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(self._preview_image)
        painter.setPen(QPen(self.app_state.primary_color))

        rect = self._get_shape_rect(force_square)
        self._draw_current_shape(painter, rect)
        painter.end()
        self.canvas.update()

    def _draw_shape_to_canvas(self, force_square: bool) -> bool:
        rect = self._get_shape_rect(force_square)
        if rect.isNull():
            return False

        painter = QPainter(self.canvas.image)
        painter.setPen(QPen(self.app_state.primary_color))
        self._draw_current_shape(painter, rect)
        painter.end()
        return True

    @abstractmethod
    def _draw_current_shape(self, painter: QPainter, rect: QRect) -> None:
        return None
