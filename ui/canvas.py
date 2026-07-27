from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QImage,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QPixmap,
    QWheelEvent,
)
from PySide6.QtWidgets import QWidget

from core.document import CanvasDocument, ShapeKind
from state import AppState
from tools.ellipse import Ellipse
from tools.eraser import Eraser
from tools.eyedropper import Eyedropper
from tools.fill import Fill
from tools.pencil import Pencil
from tools.rect import Rect
from utils import config
from utils.log import get_logger

if TYPE_CHECKING:
    from tools.base_tool import BaseTool


class Canvas(QWidget):
    pixel_hovered = Signal(int, int, QColor)
    zoom_changed = Signal(int)
    history_changed = Signal(bool, bool)

    def __init__(self, app_state: AppState) -> None:
        super().__init__()
        self.app_state = app_state
        self.document = CanvasDocument(
            config.DEFAULT_WIDTH,
            config.DEFAULT_HEIGHT,
            self.app_state.secondary_color,
            history_limit=config.HISTORY_LIMIT,
            tile_cols=config.DEFAULT_TILE_COLS,
            tile_rows=config.DEFAULT_TILE_ROWS,
            tile_size=config.DEFAULT_TILE_SIZE,
        )
        self.cell_size: int = config.DEFAULT_ZOOM
        self.grid_color: QColor = config.DEFAULT_GRID_COLOR
        self.is_grid_visible: bool = True
        self._pending_undo_snapshot: QImage | None = None

        self._is_drawing: bool = False
        self._tools: dict[str, BaseTool] = self._create_tools()
        self._current_tool: BaseTool = self._tools[config.ToolType.PENCIL]

        self._checkerboard_color_1: QColor = config.CHECKERBOARD_COLOR_1
        self._checkerboard_color_2: QColor = config.CHECKERBOARD_COLOR_2
        self._checkerboard_pixmap: QPixmap = self._create_checkerboard_pixmap(16)

        self.setMouseTracking(True)
        self._connect_state()
        self._update_size()
        self._emit_history_changed()

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

    @property
    def image(self) -> QImage:
        return self.document.image

    @property
    def columns(self) -> int:
        return self.document.columns

    @property
    def rows(self) -> int:
        return self.document.rows

    @property
    def tile_size(self) -> int:
        return self.document.tile_size

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
        self.document.reset(
            columns,
            rows,
            self.app_state.secondary_color,
            clear_history=clear_history,
            tile_cols=tile_cols,
            tile_rows=tile_rows,
            tile_size=tile_size,
        )
        if clear_history:
            self._pending_undo_snapshot = None
        self._update_size()
        self._emit_history_changed()
        self.app_state.notify_image_changed()

    def load_image(self, image: QImage) -> None:
        self._pending_undo_snapshot = None
        transparent = QColor(config.COLOR_TRANSPARENT)
        self.document.load_image(image, transparent)
        self.app_state.set_secondary_color(transparent)
        self._update_size()
        self._emit_history_changed()
        self.app_state.notify_image_changed()

    def clear_canvas(self) -> None:
        if self.document.clear(self.app_state.secondary_color):
            self.update()
            self._emit_history_changed()
            self.app_state.notify_image_changed()

    def undo(self) -> None:
        if self.document.undo():
            self._update_size()
            self._emit_history_changed()
            self.app_state.notify_image_changed()

    def redo(self) -> None:
        if self.document.redo():
            self._update_size()
            self._emit_history_changed()
            self.app_state.notify_image_changed()

    def shift_image(self, direction: str) -> None:
        if self.document.shift(direction, self.app_state.secondary_color, config.SHIFT_OFFSETS):
            self.update()
            self._emit_history_changed()
            self.app_state.notify_image_changed()

    def draw_pixel(self, col: int, row: int, color: QColor) -> bool:
        if self.document.draw_pixel(col, row, color):
            self.update(QRect(col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size))
            return True
        return False

    def flood_fill(self, col: int, row: int, color: QColor) -> bool:
        return self.document.flood_fill(col, row, color)

    def pixel_color(self, col: int, row: int) -> QColor:
        return self.document.pixel_color(col, row)

    def draw_shape(
        self,
        shape_kind: ShapeKind,
        start_cell: QPoint,
        end_cell: QPoint,
        force_square: bool,
        color: QColor,
    ) -> bool:
        return self.document.draw_shape(
            shape_kind,
            start_cell.x(),
            start_cell.y(),
            end_cell.x(),
            end_cell.y(),
            force_square,
            color,
        )

    def create_shape_preview(
        self,
        shape_kind: ShapeKind,
        start_cell: QPoint,
        end_cell: QPoint,
        force_square: bool,
        color: QColor,
    ) -> QImage:
        return self.document.create_shape_preview(
            shape_kind,
            start_cell.x(),
            start_cell.y(),
            end_cell.x(),
            end_cell.y(),
            force_square,
            color,
        )

    def _on_secondary_color_change(self, new_bg_color: QColor) -> None:
        if self.document.replace_background(new_bg_color):
            self.update()
            self._emit_history_changed()
            self.app_state.notify_image_changed()

    def _push_undo_snapshot(self, snapshot: QImage) -> None:
        self.document.commit_snapshot(snapshot)
        self._emit_history_changed()

    def _commit_pending_undo(self) -> None:
        if self._pending_undo_snapshot is None:
            return
        self._push_undo_snapshot(self._pending_undo_snapshot)
        self._pending_undo_snapshot = None

    def _update_size(self) -> None:
        width = self.columns * self.cell_size + 1
        height = self.rows * self.cell_size + 1
        self.setFixedSize(width, height)
        self.update()

    def _emit_history_changed(self) -> None:
        self.history_changed.emit(self.document.can_undo, self.document.can_redo)

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
            color = self.pixel_color(cell.x(), cell.y())
            self.app_state.set_primary_color(color)
            self.app_state.set_tool(config.ToolType.PENCIL)
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        snapshot = self.document.create_snapshot()
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
            self.pixel_hovered.emit(cell.x(), cell.y(), self.pixel_color(cell.x(), cell.y()))
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
