from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import (
    QBitmap, QColor, QImage, QMouseEvent, QPainter, QPaintEvent, QPen,
    QPixmap, QWheelEvent,
)
from PySide6.QtWidgets import QWidget

from state import AppState
from utils import config
from utils.log import get_logger

from tools.ellipse import Ellipse
from tools.eraser import Eraser
from tools.eyedropper import Eyedropper
from tools.fill import Fill
from tools.pencil import Pencil
from tools.rect import Rect

if TYPE_CHECKING:
    from tools.base_tool import BaseTool


class Canvas(QWidget):
    pixel_hovered = Signal(int, int, QColor)
    zoom_changed = Signal(int)

    def __init__(self, app_state: AppState) -> None:
        super().__init__()
        self.app_state = app_state
        self.image: QImage = QImage()
        self.columns: int = 0
        self.rows: int = 0
        self.cell_size: int = config.DEFAULT_ZOOM
        self.grid_color: QColor = config.DEFAULT_GRID_COLOR
        self.is_grid_visible: bool = True
        self.tile_cols: int = config.DEFAULT_TILE_COLS
        self.tile_rows: int = config.DEFAULT_TILE_ROWS
        self.tile_size: int = config.DEFAULT_TILE_SIZE
        self._current_bg_color: QColor = self.app_state.secondary_color

        self._undo_stack: list[QImage] = []
        self._redo_stack: list[QImage] = []
        self._pending_undo_snapshot: QImage | None = None

        self._is_drawing: bool = False
        self._tools: dict[str, BaseTool] = self._create_tools()
        self._current_tool: BaseTool = self._tools[config.ToolType.PENCIL]

        self._checkerboard_color_1: QColor = config.CHECKERBOARD_COLOR_1
        self._checkerboard_color_2: QColor = config.CHECKERBOARD_COLOR_2
        self._checkerboard_pixmap: QPixmap = self._create_checkerboard_pixmap(16)

        self.setMouseTracking(True)
        self._connect_state()
        self.reset_canvas(config.DEFAULT_WIDTH, config.DEFAULT_HEIGHT, clear_history=True)

    def _create_checkerboard_pixmap(self, size: int) -> QPixmap:
        pixmap = QPixmap(size * 2, size * 2)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        color1 = self._checkerboard_color_1
        color2 = self._checkerboard_color_2
        painter.fillRect(0, 0, size, size, color1)
        painter.fillRect(size, size, size, size, color1)
        painter.fillRect(size, 0, size, size, color2)
        painter.fillRect(0, size, size, size, color2)
        painter.end()
        return pixmap

    def _create_tools(self) -> dict[str, BaseTool]:
        return {
            config.ToolType.PENCIL: Pencil(self, self.app_state),
            config.ToolType.ERASER: Eraser(self, self.app_state),
            config.ToolType.FILL: Fill(self, self.app_state),
            config.ToolType.EYEDROPPER: Eyedropper(self, self.app_state),
            config.ToolType.RECT: Rect(self, self.app_state),
            config.ToolType.ELLIPSE: Ellipse(self, self.app_state),
        }

    def _connect_state(self) -> None:
        self.app_state.tool_changed.connect(self.set_tool)
        self.app_state.secondary_color_changed.connect(self._on_secondary_color_change)

    def set_tool(self, tool_name: str) -> None:
        if tool_name in self._tools:
            self._current_tool = self._tools[tool_name]
            self.setCursor(self._current_tool.get_cursor())
        else:
            get_logger().warning(config.MSG_TOOL_WARNING_FMT.format(tool_name=tool_name))

    def reset_canvas(
            self, columns: int, rows: int, clear_history: bool = False,
            tile_cols: int = 0, tile_rows: int = 0, tile_size: int = 0,
    ) -> None:
        self.columns, self.rows = columns, rows
        if tile_cols:
            self.tile_cols = tile_cols
        if tile_rows:
            self.tile_rows = tile_rows
        if tile_size:
            self.tile_size = tile_size
        self.image = QImage(self.columns, self.rows, QImage.Format.Format_ARGB32)
        self._current_bg_color = self.app_state.secondary_color
        self.image.fill(self.app_state.secondary_color)

        if clear_history:
            self._undo_stack.clear()
            self._redo_stack.clear()
            self._pending_undo_snapshot = None
        self._update_size()
        self.app_state.notify_image_changed()

    def load_image(self, image: QImage) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._pending_undo_snapshot = None
        self.image = image.convertToFormat(QImage.Format.Format_ARGB32)
        self.columns, self.rows = self.image.width(), self.image.height()

        transparent = QColor(config.COLOR_TRANSPARENT)
        self._current_bg_color = transparent
        self.app_state.set_secondary_color(transparent)

        self._current_bg_color = self.app_state.secondary_color
        self._update_size()
        self.app_state.notify_image_changed()

    def clear_canvas(self) -> None:
        self._push_undo()
        self.image.fill(self.app_state.secondary_color)
        self.update()
        self.app_state.notify_image_changed()

    def undo(self) -> None:
        self._traverse_history(self._undo_stack, self._redo_stack)

    def redo(self) -> None:
        self._traverse_history(self._redo_stack, self._undo_stack)

    def shift_image(self, direction: str) -> None:
        dx, dy = config.SHIFT_OFFSETS.get(direction, (0, 0))

        if dx == 0 and dy == 0:
            return

        self._push_undo()

        temp_image = QImage(self.image.size(), QImage.Format.Format_ARGB32)
        temp_image.fill(self.app_state.secondary_color)

        painter = QPainter(temp_image)
        painter.drawImage(QPoint(dx, dy), self.image)
        painter.end()

        self.image = temp_image
        self.update()
        self.app_state.notify_image_changed()

    def draw_pixel(self, col: int, row: int, color: QColor) -> bool:
        if 0 <= col < self.columns and 0 <= row < self.rows and self.image.pixelColor(col, row) != color:
            self.image.setPixelColor(col, row, color)
            self.update(QRect(col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size))
            return True
        return False

    def _on_secondary_color_change(self, new_bg_color: QColor) -> None:
        if (not new_bg_color.isValid()
                or new_bg_color == self._current_bg_color):
            return
        self._push_undo()

        # Create a mask of the old background color
        mask = self.image.createMaskFromColor(self._current_bg_color.rgb(), Qt.MaskMode.MaskOutColor)
        # Use QPainter to fill the masked area with the new color
        painter = QPainter(self.image)
        painter.setPen(new_bg_color)
        painter.setBrush(new_bg_color)
        painter.drawPixmap(self.image.rect(), QBitmap.fromImage(mask), mask.rect())
        painter.end()

        self._current_bg_color = new_bg_color
        self.update()
        self.app_state.notify_image_changed()

    def _push_undo(self) -> None:
        self._push_undo_snapshot(self.image.copy())

    def _push_undo_snapshot(self, snapshot: QImage) -> None:
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > config.HISTORY_LIMIT:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _commit_pending_undo(self) -> None:
        if self._pending_undo_snapshot is None:
            return
        self._push_undo_snapshot(self._pending_undo_snapshot)
        self._pending_undo_snapshot = None

    def _traverse_history(
            self,
            source_stack: list[QImage],
            dest_stack: list[QImage]
    ) -> None:
        if not source_stack:
            return

        dest_stack.append(self.image.copy())
        self.image = source_stack.pop()
        self.columns, self.rows = self.image.width(), self.image.height()
        self._update_size()
        self.app_state.notify_image_changed()

    def _update_size(self) -> None:
        width = self.columns * self.cell_size + 1
        height = self.rows * self.cell_size + 1
        self.setFixedSize(width, height)
        self.update()

    def set_cell_size(self, size: int) -> None:
        size = max(1, min(50, size))
        if size != self.cell_size:
            self.cell_size = size
            self._update_size()
            self.zoom_changed.emit(size)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.drawTiledPixmap(self.rect(), self._checkerboard_pixmap)

        target_rect = QRect(0, 0, self.columns * self.cell_size, self.rows * self.cell_size)
        painter.drawImage(target_rect, self.image)

        self._current_tool.paint(painter)

        if self._is_drawing and hasattr(self._current_tool, '_shape_end_pos'):
            cell_pos = getattr(self._current_tool, '_shape_end_pos', None)

            if cell_pos is not None:
                painter.setPen(QPen(Qt.GlobalColor.red, 1))
                pixel_x = cell_pos.x() * self.cell_size
                pixel_y = cell_pos.y() * self.cell_size
                painter.drawRect(pixel_x, pixel_y, self.cell_size - 1, self.cell_size - 1)

        if self.is_grid_visible and self.cell_size >= 4:
            self._draw_grid(painter, target_rect)

    def _draw_grid(self, painter: QPainter, target_rect: QRect) -> None:
        width, height, step = target_rect.width(), target_rect.height(), self.cell_size
        painter.setPen(QPen(self.grid_color, 1))
        for x in range(0, width + 1, step):
            painter.drawLine(x, 0, x, height)
        for y in range(0, height + 1, step):
            painter.drawLine(0, y, width, y)

        if self.tile_size > 1:
            painter.setPen(QPen(self.grid_color, 2))
            tile_step = step * self.tile_size
            for x in range(0, width + 1, tile_step):
                painter.drawLine(x, 0, x, height)
            for y in range(0, height + 1, tile_step):
                painter.drawLine(0, y, width, y)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        cell = QPoint(pos.x() // self.cell_size, pos.y() // self.cell_size)

        if not (0 <= cell.x() < self.columns and 0 <= cell.y() < self.rows):
            return

        if event.button() == Qt.MouseButton.RightButton:
            color = QColor(self.image.pixel(cell))
            self.app_state.set_primary_color(color)
            self.app_state.set_tool(config.ToolType.PENCIL)
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        snapshot = self.image.copy()
        if self._current_tool.is_drag_tool:
            self._pending_undo_snapshot = snapshot
            self._is_drawing = True
            changed = self._current_tool.mousePressEvent(event, cell)
            if changed:
                self._commit_pending_undo()
                self.app_state.notify_image_changed()
            return

        if self._current_tool.mousePressEvent(event, cell):
            self._push_undo_snapshot(snapshot)
            self.app_state.notify_image_changed()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        cell = QPoint(pos.x() // self.cell_size, pos.y() // self.cell_size)

        if 0 <= cell.x() < self.columns and 0 <= cell.y() < self.rows:
            self.pixel_hovered.emit(cell.x(), cell.y(), QColor(self.image.pixel(cell)))
            if self._is_drawing:
                changed = self._current_tool.mouseMoveEvent(event, cell)
                if changed:
                    self._commit_pending_undo()
                    self.app_state.notify_image_changed()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if not self._is_drawing:
            return

        pos = event.position().toPoint()
        cell = QPoint(pos.x() // self.cell_size, pos.y() // self.cell_size)
        changed = self._current_tool.mouseReleaseEvent(event, cell)
        if changed:
            self._commit_pending_undo()
            self.app_state.notify_image_changed()

        self._is_drawing = False
        self._pending_undo_snapshot = None

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y() // 120
        if delta != 0:
            self.set_cell_size(self.cell_size + delta)
            event.accept()
