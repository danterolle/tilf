from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QImage, QMouseEvent, QPainter

from core.document import ShapeKind
from state import AppState
from tools.base_tool import BaseTool

if TYPE_CHECKING:
    from ui.canvas import Canvas


class Shape(BaseTool):
    is_drag_tool = True
    shape_kind: ShapeKind

    def __init__(self, canvas: Canvas, app_state: AppState) -> None:
        super().__init__(canvas, app_state)
        self._shape_start_pos: QPoint | None = None
        self._shape_end_pos: QPoint | None = None
        self._preview_image: QImage | None = None

    def mousePressEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        self._shape_start_pos = cell
        self._preview_image = None
        return False

    def mouseMoveEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        if self._shape_start_pos is None:
            return False

        self._shape_end_pos = cell
        self._preview_image = self.canvas.create_shape_preview(
            self.shape_kind,
            self._shape_start_pos,
            self._shape_end_pos,
            bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier),
            self.app_state.primary_color,
        )
        self.canvas.update()
        return False

    def mouseReleaseEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        if self._shape_start_pos is None:
            return False

        self._shape_end_pos = cell
        changed = self.canvas.draw_shape(
            self.shape_kind,
            self._shape_start_pos,
            self._shape_end_pos,
            bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier),
            self.app_state.primary_color,
        )
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
