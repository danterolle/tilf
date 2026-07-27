from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QImage, QPainter


class CanvasDocument:
    def __init__(
        self,
        columns: int,
        rows: int,
        background_color: QColor,
        *,
        history_limit: int,
        tile_cols: int,
        tile_rows: int,
        tile_size: int,
    ) -> None:
        self.history_limit = history_limit
        self.tile_cols = tile_cols
        self.tile_rows = tile_rows
        self.tile_size = tile_size
        self.background_color = background_color
        self.image = QImage()
        self.columns = 0
        self.rows = 0
        self._undo_stack: list[QImage] = []
        self._redo_stack: list[QImage] = []
        self.reset(columns, rows, background_color, clear_history=True)

    def reset(
        self,
        columns: int,
        rows: int,
        background_color: QColor,
        *,
        clear_history: bool = False,
        tile_cols: int = 0,
        tile_rows: int = 0,
        tile_size: int = 0,
    ) -> None:
        self.columns = columns
        self.rows = rows
        if tile_cols:
            self.tile_cols = tile_cols
        if tile_rows:
            self.tile_rows = tile_rows
        if tile_size:
            self.tile_size = tile_size

        self.background_color = background_color
        self.image = QImage(self.columns, self.rows, QImage.Format.Format_ARGB32)
        self.image.fill(background_color)

        if clear_history:
            self.clear_history()

    def load_image(self, image: QImage, background_color: QColor) -> None:
        self.clear_history()
        self.image = image.convertToFormat(QImage.Format.Format_ARGB32)
        self.columns = self.image.width()
        self.rows = self.image.height()
        self.background_color = background_color

    def clear_history(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()

    def create_snapshot(self) -> QImage:
        return self.image.copy()

    def commit_snapshot(self, snapshot: QImage) -> None:
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > self.history_limit:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def clear(self, background_color: QColor) -> bool:
        self.commit_snapshot(self.create_snapshot())
        self.background_color = background_color
        self.image.fill(background_color)
        return True

    def draw_pixel(self, col: int, row: int, color: QColor) -> bool:
        if not self.contains(col, row) or self.image.pixelColor(col, row) == color:
            return False

        self.image.setPixelColor(col, row, color)
        return True

    def flood_fill(self, start_col: int, start_row: int, new_color: QColor) -> bool:
        if not self.contains(start_col, start_row):
            return False

        target_rgba = self.image.pixel(start_col, start_row)
        new_rgba = new_color.rgba()
        if target_rgba == new_rgba:
            return False

        stack = [(start_col, start_row)]
        while stack:
            col, row = stack.pop()
            if self.contains(col, row) and self.image.pixel(col, row) == target_rgba:
                self.image.setPixel(col, row, new_rgba)
                stack.extend([(col + 1, row), (col - 1, row), (col, row + 1), (col, row - 1)])

        return True

    def shift(self, direction: str, background_color: QColor, offsets: Mapping[str, tuple[int, int]]) -> bool:
        dx, dy = offsets.get(direction, (0, 0))
        if dx == 0 and dy == 0:
            return False

        self.commit_snapshot(self.create_snapshot())

        shifted_image = QImage(self.image.size(), QImage.Format.Format_ARGB32)
        shifted_image.fill(background_color)

        painter = QPainter(shifted_image)
        painter.drawImage(QPoint(dx, dy), self.image)
        painter.end()

        self.image = shifted_image
        self.background_color = background_color
        return True

    def replace_background(self, new_background_color: QColor) -> bool:
        if not new_background_color.isValid() or new_background_color == self.background_color:
            return False

        previous_background_color = self.background_color
        snapshot = self.create_snapshot()
        changed = False

        for row in range(self.rows):
            for col in range(self.columns):
                if self.image.pixelColor(col, row) == previous_background_color:
                    self.image.setPixelColor(col, row, new_background_color)
                    changed = True

        if not changed:
            self.background_color = new_background_color
            return False

        self.commit_snapshot(snapshot)
        self.background_color = new_background_color
        return True

    def undo(self) -> bool:
        return self._traverse_history(self._undo_stack, self._redo_stack)

    def redo(self) -> bool:
        return self._traverse_history(self._redo_stack, self._undo_stack)

    def contains(self, col: int, row: int) -> bool:
        return 0 <= col < self.columns and 0 <= row < self.rows

    def _traverse_history(self, source_stack: list[QImage], dest_stack: list[QImage]) -> bool:
        if not source_stack:
            return False

        dest_stack.append(self.image.copy())
        self.image = source_stack.pop()
        self.columns = self.image.width()
        self.rows = self.image.height()
        return True
