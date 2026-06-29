from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QMouseEvent, QPainter, QImage, QPen, QCursor

from state import AppState
from tools.base_tool import BaseTool

if TYPE_CHECKING:
    from ui.canvas import Canvas


class Line(BaseTool):
    def __init__(self, canvas: Canvas, app_state: AppState):
        super().__init__(canvas, app_state)
        self._start_pos: QPoint | None = None
        self._end_pos: QPoint | None = None
        self._preview_image: QImage | None = None

    def mousePressEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        self._start_pos = cell
        self._end_pos = cell
        self._preview_image = QImage(self.canvas.image.size(), QImage.Format.Format_ARGB32)
        self._preview_image.fill(Qt.GlobalColor.transparent)
        return True

    def mouseMoveEvent(self, event: QMouseEvent, cell: QPoint):
        if not self._start_pos:
            return
        self._end_pos = cell
        self._draw_preview(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)

    def mouseReleaseEvent(self, event: QMouseEvent, cell: QPoint):
        if not self._start_pos:
            return
        self._end_pos = cell
        self._draw_to_canvas(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        self._preview_image = None
        self._start_pos = None
        self._end_pos = None
        self.canvas.update()

    def paint(self, painter: QPainter):
        if self._preview_image:
            target_rect = QRect(
                0, 0,
                self.canvas.columns * self.canvas.cell_size,
                self.canvas.rows * self.canvas.cell_size,
            )
            painter.drawImage(target_rect, self._preview_image)

    def _clamp(self, p: QPoint) -> QPoint:
        return QPoint(
            max(0, min(self.canvas.columns - 1, p.x())),
            max(0, min(self.canvas.rows - 1, p.y())),
        )

    def _constrain_line(self) -> None:
        if self._start_pos is None or self._end_pos is None:
            return
        x1, y1 = self._start_pos.x(), self._start_pos.y()
        x2, y2 = self._end_pos.x(), self._end_pos.y()
        dx = x2 - x1
        dy = y2 - y1
        adx, ady = abs(dx), abs(dy)
        if adx > ady:
            y2 = y1
        elif ady > adx:
            x2 = x1
        self._end_pos = self._clamp(QPoint(x2, y2))

    def _draw_preview(self, constrain: bool) -> None:
        if not self._preview_image:
            return
        self._preview_image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(self._preview_image)
        painter.setPen(QPen(self.app_state.primary_color))

        if constrain:
            self._constrain_line()
        if self._start_pos and self._end_pos:
            painter.drawLine(self._start_pos, self._end_pos)
        painter.end()
        self.canvas.update()

    def _draw_to_canvas(self, constrain: bool) -> None:
        painter = QPainter(self.canvas.image)
        painter.setPen(QPen(self.app_state.primary_color))

        if constrain:
            self._constrain_line()
        if self._start_pos and self._end_pos:
            painter.drawLine(self._start_pos, self._end_pos)
        painter.end()

    def get_cursor(self) -> QCursor:
        return QCursor(Qt.CursorShape.CrossCursor)
