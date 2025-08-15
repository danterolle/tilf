from __future__ import annotations
from typing import Dict, List, TYPE_CHECKING
from PySide6.QtCore import Qt, QRect, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QImage, QPaintEvent, QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QWidget
from state import AppState
import config

if TYPE_CHECKING:
    from tools.base_tool import BaseTool
# Why TYPE_CHECKING?
# A "circular import" error had occurred.
#
# canvas.py could import the tool classes (like Pencil, Eraser, etc...) from the tools module,
# but the tool classes imported the Canvas class from this same file.
#
# This can create an ugly _dependency cycle_ that Python could **not** resolve at startup,
# causing a "circular import" error.
#
# One solution is to import types only during static analysis.
# That's because `TYPE_CHECKING` is set to `True` only when a type checker
# is analyzing the code, while it is `False` during normal execution.
#
# For more: https://docs.python.org/3/library/typing.html#typing.TYPE_CHECKING

class Canvas(QWidget):
    pixel_hovered = Signal(int, int, QColor)
    zoom_changed = Signal(int)

    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state
        self.image: QImage = QImage()
        self.columns: int = 0
        self.rows: int = 0
        self.cell_size: int = config.DEFAULT_ZOOM
        self.grid_color: QColor = config.DEFAULT_GRID_COLOR
        self.is_grid_visible: bool = True
        self._current_bg_color: QColor = self.app_state.secondary_color

        self._undo_stack: List[QImage] = []
        self._redo_stack: List[QImage] = []

        self._is_drawing: bool = False
        self._tools: Dict[str, BaseTool] = self._create_tools()
        self._current_tool: BaseTool = self._tools["pencil"]

        self.setMouseTracking(True)
        self._connect_state()
        self.reset_canvas(config.DEFAULT_WIDTH, config.DEFAULT_HEIGHT, clear_history=True)

    # https://peps.python.org/pep-0484/#forward-references
    #
    # Since `BaseTool` is imported only inside the `TYPE_CHECKING` block,
    # it is not directly available at runtime here.
    #
    # So, by using the class name as a string ('BaseTool'),
    # instead of the actual type (BaseTool),
    # we are able to create the tool instances later.
    #
    # Remember: the type hint is _only_ used for type checking,
    # not for runtime usage.
    #
    #### OR
    #
    # place `from __future__ import annotations` at the top of the file.
    # It will postpone the evaluation of type hints:
    # annotations automatically become strings and are resolved
    # only by type checkers, and not at runtime.
    def _create_tools(self) -> Dict[str, BaseTool]:
        # The imports of the concrete tool classes are moved here,
        # inside the method instead of at the module level.
        #
        # Why? This postpones their import until the `_create_tools` method is
        # _actually_ called. At that point, the `canvas` module has already been
        # fully loaded, and the tools can import `Canvas` without issues,
        #
        # thus breaking the dependency cycle.
        from tools.pencil import Pencil
        from tools.eraser import Eraser
        from tools.fill import Fill
        from tools.eyedropper import Eyedropper
        from tools.rect import Rect
        from tools.ellipse import Ellipse

        return {
            "pencil": Pencil(self, self.app_state),
            "eraser": Eraser(self, self.app_state),
            "fill": Fill(self, self.app_state),
            "eyedropper": Eyedropper(self, self.app_state),
            "rect": Rect(self, self.app_state),
            "ellipse": Ellipse(self, self.app_state),
        }

    def _connect_state(self) -> None:
        self.app_state.tool_changed.connect(self.set_tool)
        self.app_state.secondary_color_changed.connect(self._on_secondary_color_change)

    def set_tool(self, tool_name: str) -> None:
        if tool_name in self._tools:
            self._current_tool = self._tools[tool_name]
            self.setCursor(self._current_tool.get_cursor())
        else:
            print(f"Warning: Tool '{tool_name}' not found.")

    def reset_canvas(self, columns: int, rows: int, clear_history: bool = False) -> None:
        self.columns, self.rows = columns, rows
        self.image = QImage(self.columns, self.rows, QImage.Format.Format_ARGB32)
        self._current_bg_color = self.app_state.secondary_color
        self.image.fill(self.app_state.secondary_color)

        if clear_history:
            self._undo_stack.clear()
            self._redo_stack.clear()
        self._update_size()
        self.app_state.notify_image_changed()

    def load_image(self, image: QImage) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.image = image.convertToFormat(QImage.Format.Format_ARGB32)
        self.columns, self.rows = self.image.width(), self.image.height()
        # Assume transparent images have a transparent background color
        self.app_state.set_secondary_color(QColor("transparent"))
        self._current_bg_color = self.app_state.secondary_color
        self._push_undo()
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
        self._push_undo()

        offsets = {
            "right": (1, 0),
            "left": (-1, 0),
            "down": (0, 1),
            "up": (0, -1)
        }
        dx, dy = offsets.get(direction, (0, 0))

        if dx == 0 and dy == 0:
            return

        temp_image = QImage(self.image.size(), QImage.Format.Format_ARGB32)
        temp_image.fill(self.app_state.secondary_color)

        painter = QPainter(temp_image)
        painter.drawImage(QPoint(dx, dy), self.image)
        painter.end()

        self.image = temp_image
        self.update()
        self.app_state.notify_image_changed()

    def draw_pixel(self, col: int, row: int, color: QColor) -> None:
        if 0 <= col < self.columns and 0 <= row < self.rows and self.image.pixelColor(col, row) != color:
            self.image.setPixelColor(col, row, color)
            return self.update(QRect(col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size))
        return None

    def _on_secondary_color_change(self, new_bg_color: QColor) -> None:
        if not new_bg_color.isValid() or new_bg_color == self._current_bg_color:
            return

        self._push_undo()

        old_color_rgba = self._current_bg_color.rgba()
        new_color_rgba = new_bg_color.rgba()

        # Iterate through the image and replace the old background color.
        #
        # Problem:
        # This double loop iterates over _every single pixel_ of the image
        # using Python method calls. For a 256x256 image, that’s
        # 65,536 iterations. For a 1024x1024 image, over a million.
        # And pixel-by-pixel operations in Python are notoriously **slow**.
        #
        # TODO:
        # We could create a mask based on the color we want to replace,
        # then use QPainter to **fill** only the areas defined by that mask.
        for y in range(self.image.height()):
            for x in range(self.image.width()):
                if self.image.pixel(x, y) == old_color_rgba:
                    self.image.setPixel(x, y, new_color_rgba)

        self._current_bg_color = new_bg_color
        self.update()
        self.app_state.notify_image_changed()

    def _push_undo(self) -> None:
        self._undo_stack.append(self.image.copy())
        if len(self._undo_stack) > config.HISTORY_LIMIT:
            self._undo_stack.pop(0)
        return self._redo_stack.clear()

    def _traverse_history(
            self,
            source_stack: List[QImage],
            dest_stack: List[QImage]
    ) -> None:
        if not source_stack: return
        dest_stack.append(self.image.copy())
        self.image = source_stack.pop()
        self.columns, self.rows = self.image.width(), self.image.height()
        self._update_size()
        self.app_state.notify_image_changed()

    def _update_size(self) -> None:
        width = self.columns * self.cell_size + 1
        height = self.rows * self.cell_size + 1
        self.setMinimumSize(width, height)
        self.resize(width, height)
        self.update()

    def set_cell_size(self, size: int) -> None:
        size = max(1, min(50, size))
        if size != self.cell_size:
            self.cell_size = size
            self._update_size()
            self.zoom_changed.emit(size)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        self._draw_checkerboard_background(painter)

        target_rect = QRect(0, 0, self.columns * self.cell_size, self.rows * self.cell_size)
        painter.drawImage(target_rect, self.image)

        self._current_tool.paint(painter)

        if self._is_drawing and hasattr(self._current_tool, '_shape_end_pos'):
            cell_pos = getattr(self._current_tool, '_shape_end_pos', None)

            if cell_pos:
                painter.setPen(QPen(Qt.GlobalColor.red, 1))
                pixel_x = cell_pos.x() * self.cell_size
                pixel_y = cell_pos.y() * self.cell_size
                painter.drawRect(pixel_x, pixel_y, self.cell_size - 1, self.cell_size - 1)

        if self.is_grid_visible and self.cell_size >= 4:
            self._draw_grid(painter, target_rect)

    def _draw_checkerboard_background(self, painter: QPainter) -> None:
        checker_size = 8
        # TODO:
        # This double loop draws many small rectangles
        # to cover the entire area of the widget.
        # It is rerun from scratch _every single time the widget repaints_.
        for y in range(0, self.height(), checker_size):
            for x in range(0, self.width(), checker_size):
                color = config.CHECKERBOARD_COLOR_1 \
                    if (x // checker_size + y // checker_size) % 2 == 0 \
                    else config.CHECKERBOARD_COLOR_2
                painter.fillRect(x, y, checker_size, checker_size, color)

    def _draw_grid(self, painter: QPainter, target_rect: QRect) -> None:
        painter.setPen(QPen(self.grid_color))
        width, height, step = target_rect.width(), target_rect.height(), self.cell_size
        for x in range(0, width + 1, step): painter.drawLine(x, 0, x, height)
        for y in range(0, height + 1, step): painter.drawLine(0, y, width, y)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        cell = QPoint(pos.x() // self.cell_size, pos.y() // self.cell_size)

        if not (0 <= cell.x() < self.columns and 0 <= cell.y() < self.rows):
            return

        if event.button() == Qt.MouseButton.RightButton:
            color = QColor(self.image.pixel(cell))
            self.app_state.set_primary_color(color)
            self.app_state.set_tool("pencil")
            return

        self._is_drawing = True
        self._push_undo()
        self._current_tool.mousePressEvent(event, cell)
        self.app_state.notify_image_changed()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        cell = QPoint(pos.x() // self.cell_size, pos.y() // self.cell_size)

        if 0 <= cell.x() < self.columns and 0 <= cell.y() < self.rows:
            self.pixel_hovered.emit(cell.x(), cell.y(), QColor(self.image.pixel(cell)))
            if self._is_drawing:
                self._current_tool.mouseMoveEvent(event, cell)
                self.app_state.notify_image_changed()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if not self._is_drawing: return
        pos = event.position().toPoint()
        cell = QPoint(pos.x() // self.cell_size, pos.y() // self.cell_size)
        self._current_tool.mouseReleaseEvent(event, cell)
        self._is_drawing = False

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y() // 120
        if delta != 0:
            self.set_cell_size(self.cell_size + delta)
            event.accept()