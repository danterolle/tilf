from abc import abstractmethod
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QMouseEvent, QPainter, QImage, QPen

from state import AppState
from tools.base_tool import BaseTool
from ui.canvas import Canvas


class Shape(BaseTool):
    def __init__(self, canvas: Canvas, app_state: AppState):
        super().__init__(canvas, app_state)
        self._shape_start_pos: QPoint | None = None
        self._shape_end_pos: QPoint | None = None
        self._preview_image: QImage | None = None

    def mousePressEvent(self, event: QMouseEvent, cell: QPoint):
        self._shape_start_pos = cell
        self._preview_image = QImage(self.canvas.image.size(), QImage.Format.Format_ARGB32)
        self._preview_image.fill(Qt.GlobalColor.transparent)

    def mouseMoveEvent(self, event: QMouseEvent, cell: QPoint):
        if not self._preview_image: return
        self._shape_end_pos = cell
        self._draw_shape_preview(bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier))

    def mouseReleaseEvent(self, event: QMouseEvent, cell: QPoint):
        if not self._shape_start_pos: return
        self._shape_end_pos = cell
        self._draw_shape_to_canvas(bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier))
        self._preview_image = None
        self._shape_start_pos = None
        self._shape_end_pos = None
        self.canvas.update()

    def paint(self, painter: QPainter):
        if self._preview_image:
            target_rect = QRect(
                0,
                0,
                self.canvas.columns * self.canvas.cell_size,
                self.canvas.rows * self.canvas.cell_size
            )
            painter.drawImage(target_rect, self._preview_image)

    def _get_shape_rect(self, force_square: bool) -> QRect:
        if not self._shape_start_pos or not self._shape_end_pos:
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

    def _draw_shape_preview(self, force_square: bool):
        if not self._preview_image: return
        self._preview_image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(self._preview_image)
        painter.setPen(QPen(self.app_state.primary_color))

        rect = self._get_shape_rect(force_square)
        self._draw_current_shape(painter, rect)
        painter.end()
        self.canvas.update()

    def _draw_shape_to_canvas(self, force_square: bool):
        painter = QPainter(self.canvas.image)
        painter.setPen(QPen(self.app_state.primary_color))

        rect = self._get_shape_rect(force_square)
        self._draw_current_shape(painter, rect)
        painter.end()

    @abstractmethod
    def _draw_current_shape(self, painter: QPainter, rect: QRect):
        pass