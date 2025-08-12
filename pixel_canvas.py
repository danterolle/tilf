from typing import Optional, List

from PySide6.QtCore import Qt, QRect, Signal, QPoint
from PySide6.QtGui import (
    QPainter, QColor, QPen, QImage, QPaintEvent, QMouseEvent
)
from PySide6.QtWidgets import QWidget


class PixelCanvas(QWidget):
    pixel_hovered = Signal(int, int, QColor)
    zoom_changed = Signal(int)
    image_changed = Signal()
    color_picked = Signal(QColor)
    tool_change_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.image = None
        self.base_color = QColor("white")
        self.rows: int = 16
        self.columns: int = 16
        self.cell_size: int = 32
        self.current_color = QColor("black")
        self.grid_color = QColor(80, 80, 80, 160)
        self.is_grid_visible: bool = True
        self.current_tool: str = "pencil"
        self._is_drawing: bool = False
        self._undo_stack: List[QImage] = []
        self._redo_stack: List[QImage] = []
        self._history_limit: int = 50
        self._shape_start_pos: Optional[QPoint] = None
        self._shape_end_pos: Optional[QPoint] = None
        self._preview_image: Optional[QImage] = None
        self._pencil_draw_color: Optional[QColor] = None
        self.reset_canvas(self.columns, self.columns, clear_history=True)
        self._update_cursor()

    def reset_canvas(self, columns: int, rows: int, clear_history: bool = False) -> None:
        self.columns, self.rows = columns, rows
        self.base_color = QColor("white")
        self.image = QImage(self.columns, self.rows, QImage.Format.Format_ARGB32)
        self.image.fill(self.base_color)
        if clear_history: self._undo_stack.clear(); self._redo_stack.clear()
        self._update_size()
        self.image_changed.emit()

    def _update_size(self) -> None:
        width = self.columns * self.cell_size + 1
        height = self.rows * self.cell_size + 1
        self.setMinimumSize(width, height)
        self.resize(width, height)
        self.update()

    def _update_cursor(self) -> None:
        cursors = {
            "pencil": Qt.CursorShape.CrossCursor,
            "eraser": Qt.CursorShape.PointingHandCursor,
            "fill": Qt.CursorShape.UpArrowCursor,
            "eyedropper": Qt.CursorShape.CrossCursor,
            "rect": Qt.CursorShape.CrossCursor,
            "ellipse": Qt.CursorShape.CrossCursor
        }
        self.setCursor(cursors.get(self.current_tool, Qt.CursorShape.ArrowCursor))

    def set_tool(self, tool: str) -> None:
        self.current_tool = tool
        self._update_cursor()

    def clear_canvas(self, emit_change: bool = True) -> None:
        self._push_undo()
        self.image.fill(self.base_color)
        self.update()
        if emit_change: self.image_changed.emit()

    def set_background_color(self, color: QColor) -> None:
        if not color.isValid() or color == self.base_color:
            return

        self._push_undo()
        old_color_rgba = self.base_color.rgba()
        new_color_rgba = color.rgba()
        self.base_color = color

        for y in range(self.image.height()):
            for x in range(self.image.width()):
                if self.image.pixel(x, y) == old_color_rgba:
                    self.image.setPixel(x, y, new_color_rgba)

        self.update()
        self.image_changed.emit()

    def set_canvas_size(self, columns: int, rows: int) -> None:
        self._push_undo()
        new_image = QImage(columns, rows, QImage.Format.Format_ARGB32)
        new_image.fill(self.base_color)
        painter = QPainter(new_image)
        painter.drawImage(0, 0, self.image)
        painter.end()
        self.image = new_image
        self.columns, self.rows = columns, rows
        self._update_size()
        self.image_changed.emit()

    def set_cell_size(self, size: int) -> None:
        size = max(1, min(50, size))
        if size != self.cell_size:
            self.cell_size = size
            self._update_size()
            self.zoom_changed.emit(size)

    def load_image(self, img: QImage) -> None:
        if img.isNull(): return
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.image = img.convertToFormat(QImage.Format.Format_ARGB32)
        self.columns, self.rows = self.image.width(), self.image.height()
        self.base_color = QColor("transparent")
        self._push_undo()
        self._update_size()
        self.image_changed.emit()

    def add_image_data(self, new_image: QImage) -> None:
        if new_image.isNull(): return
        self._push_undo()
        painter = QPainter(self.image)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.drawImage(0, 0, new_image)
        painter.end()
        self.update()
        self.image_changed.emit()

    def _push_undo(self) -> None:
        self._undo_stack.append(self.image.copy())
        if len(self._undo_stack) > self._history_limit: self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _traverse_history(self, source_stack: List[QImage], dest_stack: List[QImage]) -> None:
        if not source_stack:
            return
        dest_stack.append(self.image.copy())
        self.image = source_stack.pop()
        self.columns, self.rows = self.image.width(), self.image.height()
        self._update_size()
        self.image_changed.emit()

    def undo(self) -> None:
        self._traverse_history(self._undo_stack, self._redo_stack)

    def redo(self) -> None:
        self._traverse_history(self._redo_stack, self._undo_stack)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        self._draw_checkerboard_background(painter)
        target_rect = QRect(0, 0, self.columns * self.cell_size, self.rows * self.cell_size)
        painter.drawImage(target_rect, self.image)
        if self._preview_image: painter.drawImage(target_rect, self._preview_image)
        if self.is_grid_visible and self.cell_size >= 4: self._draw_grid(painter, target_rect)

    def _draw_checkerboard_background(self, painter: QPainter) -> None:
        checker_size = 8
        color1, color2 = QColor(220, 220, 220, 190), QColor(180, 180, 180, 150)
        for y in range(0, self.height(), checker_size):
            for x in range(0, self.width(), checker_size):
                color = color1 if (x // checker_size + y // checker_size) % 2 == 0 else color2
                painter.fillRect(x, y, checker_size, checker_size, color)

    def _draw_grid(self, painter: QPainter, target_rect: QRect) -> None:
        painter.setPen(QPen(self.grid_color))
        width, height, step = target_rect.width(), target_rect.height(), self.cell_size
        for x in range(0, width + 1, step): painter.drawLine(x, 0, x, height)
        for y in range(0, height + 1, step): painter.drawLine(0, y, width, y)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        col, row = pos.x() // self.cell_size, pos.y() // self.cell_size
        if not (0 <= col < self.columns and 0 <= row < self.rows): return
        color_at_pos = QColor(self.image.pixel(col, row))

        if event.button() == Qt.MouseButton.RightButton:
            self.color_picked.emit(color_at_pos)
            self.tool_change_requested.emit("pencil")
            return

        if self.current_tool == "eyedropper":
            self.color_picked.emit(color_at_pos)
            return

        self._push_undo()
        self._is_drawing = True

        if self.current_tool in ["rect", "ellipse"]:
            self._shape_start_pos = QPoint(col, row)
            self._preview_image = QImage(self.image.size(), QImage.Format.Format_ARGB32)
            self._preview_image.fill(QColor(0, 0, 0, 0))
        elif self.current_tool == "pencil":

            force_bg = bool(event.modifiers() & Qt.KeyboardModifier.AltModifier)
            if force_bg:
                self._pencil_draw_color = self.base_color
            else:
                # If the initial pixel is already the foreground color,
                # the entire brushstroke will use the background color.
                #
                # Otherwise, it will use the foreground color.
                self._pencil_draw_color = self.base_color if color_at_pos == self.current_color else self.current_color
            self._draw_at_cell(col, row, self.current_color)
        elif self.current_tool == "eraser":
            self._draw_at_cell(col, row, self.base_color)
        elif self.current_tool == "fill":
            self._flood_fill(col, row, self.current_color)
        self.image_changed.emit()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        col, row = pos.x() // self.cell_size, pos.y() // self.cell_size

        if 0 <= col < self.columns and 0 <= row < self.rows:
            self.pixel_hovered.emit(col, row, QColor(self.image.pixel(col, row)))

            if self._is_drawing:
                if self.current_tool in ["rect", "ellipse"]:
                    self._shape_end_pos = QPoint(col, row)
                    self._draw_shape_preview(event.modifiers() == Qt.KeyboardModifier.ShiftModifier)
                elif self.current_tool == "pencil":
                    # Use the "locked" color selected at mousePressEvent (Alt key, or Option on MacOS).
                    color_to_use = self._pencil_draw_color or self.current_color
                    self._draw_at_cell(col, row, color_to_use)
                elif self.current_tool == "eraser":
                    self._draw_at_cell(col, row, self.base_color)
                self.image_changed.emit()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._is_drawing and self.current_tool in ["rect", "ellipse"]:
            self._draw_shape_to_canvas(event.modifiers() == Qt.KeyboardModifier.ShiftModifier)
            self._preview_image = None
            self._shape_start_pos = None
            self._shape_end_pos = None
            self.update()
        self._is_drawing = False
        self._pencil_draw_color = None

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y() // 120
        if delta != 0: self.set_cell_size(self.cell_size + delta); event.accept()

    def _draw_at_cell(self, col: int, row: int, color: QColor) -> None:
        if 0 <= col < self.columns and 0 <= row < self.rows and QColor(self.image.pixel(col, row)) != color:
            self.image.setPixelColor(col, row, color)
            self.update(QRect(col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size))

    def _get_shape_rect(self, force_square: bool) -> QRect:
        if not self._shape_start_pos or not self._shape_end_pos: return QRect()
        x1, y1 = self._shape_start_pos.x(), self._shape_start_pos.y()
        x2, y2 = self._shape_end_pos.x(), self._shape_end_pos.y()
        if force_square:
            dx, dy = abs(x2 - x1), abs(y2 - y1)
            size = max(dx, dy)
            nx2 = x1 + size if x2 > x1 else x1 - size
            ny2 = y1 + size if y2 > y1 else y1 - size
            return QRect(QPoint(x1, y1), QPoint(nx2, ny2)).normalized()
        return QRect(self._shape_start_pos, self._shape_end_pos).normalized()

    def _draw_current_shape(self, painter: QPainter, rect: QRect) -> None:
        if self.current_tool == "rect":
            painter.drawRect(rect)
        elif self.current_tool == "ellipse":
            painter.drawEllipse(rect)

    def _draw_shape_preview(self, force_square: bool) -> None:
        if not self._preview_image: return
        self._preview_image.fill(QColor(0, 0, 0, 0))

        painter = QPainter(self._preview_image)
        painter.setPen(QPen(self.current_color))
        rect = self._get_shape_rect(force_square)
        self._draw_current_shape(painter, rect)
        painter.end()
        self.update()

    def _draw_shape_to_canvas(self, force_square: bool) -> None:
        painter = QPainter(self.image)
        painter.setPen(QPen(self.current_color))
        rect = self._get_shape_rect(force_square)
        self._draw_current_shape(painter, rect)
        painter.end()
        self.image_changed.emit()

    def _flood_fill(self, start_col: int, start_row: int, new_color: QColor) -> None:
        target_rgba = self.image.pixel(start_col, start_row)
        if target_rgba == new_color.rgba(): return
        stack = [(start_col, start_row)]
        while stack:
            col, row = stack.pop()
            if 0 <= col < self.columns and 0 <= row < self.rows and self.image.pixel(col, row) == target_rgba:
                self.image.setPixel(col, row, new_color.rgba())
                stack.extend([(col + 1, row), (col - 1, row), (col, row + 1), (col, row - 1)])
        self.update()

    def export_image(self, filename: str, file_format: Optional[str], is_transparent: bool) -> None:
        img_to_save = self.image.copy()

        if not is_transparent:
            background_img = QImage(img_to_save.size(), QImage.Format.Format_ARGB32)
            background_img.fill(QColor("white"))
            painter = QPainter(background_img)
            painter.drawImage(0, 0, img_to_save)
            painter.end()
            background_img.save(filename, file_format)
        else:
            img_to_save.save(filename, file_format)