from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import cos, pi, sin
from typing import Literal

ColorValue = int
PixelSnapshot = tuple[ColorValue, ...]
ShapeKind = Literal["rect", "ellipse"]
ShapeBounds = tuple[int, int, int, int]
TRANSPARENT_COLOR: ColorValue = 0


class CanvasDocument:
    def __init__(
        self,
        columns: int,
        rows: int,
        background_color: ColorValue,
        *,
        history_limit: int,
        tile_size: int,
    ) -> None:
        self.history_limit = history_limit
        self.tile_size = tile_size
        self.background_color = background_color
        self.columns = 0
        self.rows = 0
        self._pixels: list[ColorValue] = []
        self._undo_stack: list[PixelSnapshot] = []
        self._redo_stack: list[PixelSnapshot] = []
        self.reset(columns, rows, background_color, clear_history=True)

    @property
    def pixels(self) -> PixelSnapshot:
        return tuple(self._pixels)

    def reset(
        self,
        columns: int,
        rows: int,
        background_color: ColorValue,
        *,
        clear_history: bool = False,
        tile_size: int = 0,
    ) -> None:
        self.columns = columns
        self.rows = rows
        if tile_size:
            self.tile_size = tile_size

        self.background_color = background_color
        self._pixels = [background_color] * (columns * rows)

        if clear_history:
            self.clear_history()

    def load_pixels(
        self,
        columns: int,
        rows: int,
        pixels: Sequence[ColorValue],
        background_color: ColorValue,
    ) -> None:
        expected_size = columns * rows
        if len(pixels) != expected_size:
            raise ValueError(f"Expected {expected_size} pixels, got {len(pixels)}")

        self.clear_history()
        self.columns = columns
        self.rows = rows
        self._pixels = list(pixels)
        self.background_color = background_color

    def clear_history(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def create_snapshot(self) -> PixelSnapshot:
        return tuple(self._pixels)

    def commit_snapshot(self, snapshot: PixelSnapshot) -> None:
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > self.history_limit:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def clear(self, background_color: ColorValue) -> bool:
        self.commit_snapshot(self.create_snapshot())
        self.background_color = background_color
        self._pixels = [background_color] * (self.columns * self.rows)
        return True

    def draw_pixel(self, col: int, row: int, color: ColorValue) -> bool:
        if not self.contains(col, row):
            return False

        index = self._pixel_index(col, row)
        if self._pixels[index] == color:
            return False

        self._pixels[index] = color
        return True

    def pixel_color(self, col: int, row: int) -> ColorValue:
        if not self.contains(col, row):
            return TRANSPARENT_COLOR
        return self._pixels[self._pixel_index(col, row)]

    def flood_fill(self, start_col: int, start_row: int, new_color: ColorValue) -> bool:
        if not self.contains(start_col, start_row):
            return False

        target_color = self.pixel_color(start_col, start_row)
        if target_color == new_color:
            return False

        stack = [(start_col, start_row)]
        while stack:
            col, row = stack.pop()
            if self.contains(col, row) and self.pixel_color(col, row) == target_color:
                self._pixels[self._pixel_index(col, row)] = new_color
                stack.extend([(col + 1, row), (col - 1, row), (col, row + 1), (col, row - 1)])

        return True

    def shift(
        self,
        direction: str,
        background_color: ColorValue,
        offsets: Mapping[str, tuple[int, int]],
    ) -> bool:
        dx, dy = offsets.get(direction, (0, 0))
        if dx == 0 and dy == 0:
            return False

        self.commit_snapshot(self.create_snapshot())

        shifted_pixels = [background_color] * (self.columns * self.rows)
        for row in range(self.rows):
            for col in range(self.columns):
                target_col = col + dx
                target_row = row + dy
                if self.contains(target_col, target_row):
                    shifted_pixels[self._pixel_index(target_col, target_row)] = self.pixel_color(col, row)

        self._pixels = shifted_pixels
        self.background_color = background_color
        return True

    def draw_shape(
        self,
        shape_kind: ShapeKind,
        start_col: int,
        start_row: int,
        end_col: int,
        end_row: int,
        force_square: bool,
        color: ColorValue,
    ) -> bool:
        bounds = self.shape_bounds(start_col, start_row, end_col, end_row, force_square)
        if bounds is None:
            return False

        self._draw_shape(self._pixels, shape_kind, bounds, color)
        return True

    def create_shape_preview(
        self,
        shape_kind: ShapeKind,
        start_col: int,
        start_row: int,
        end_col: int,
        end_row: int,
        force_square: bool,
        color: ColorValue,
    ) -> PixelSnapshot:
        preview_pixels = [TRANSPARENT_COLOR] * (self.columns * self.rows)
        bounds = self.shape_bounds(start_col, start_row, end_col, end_row, force_square)
        if bounds is not None:
            self._draw_shape(preview_pixels, shape_kind, bounds, color)
        return tuple(preview_pixels)

    def shape_bounds(
        self,
        start_col: int,
        start_row: int,
        end_col: int,
        end_row: int,
        force_square: bool,
    ) -> ShapeBounds | None:
        if not self.contains(start_col, start_row):
            return None

        if force_square:
            dx = abs(end_col - start_col)
            dy = abs(end_row - start_row)
            size = max(dx, dy)
            end_col = start_col + size if end_col >= start_col else start_col - size
            end_row = start_row + size if end_row >= start_row else start_row - size

        left = max(0, min(start_col, end_col))
        top = max(0, min(start_row, end_row))
        right = min(self.columns - 1, max(start_col, end_col))
        bottom = min(self.rows - 1, max(start_row, end_row))

        width = right - left + 1
        height = bottom - top + 1
        if width <= 0 or height <= 0:
            return None

        return left, top, width, height

    def replace_background(self, new_background_color: ColorValue) -> bool:
        if new_background_color == self.background_color:
            return False

        previous_background_color = self.background_color
        snapshot = self.create_snapshot()
        changed = False

        for index, pixel in enumerate(self._pixels):
            if pixel == previous_background_color:
                self._pixels[index] = new_background_color
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

    def _traverse_history(self, source_stack: list[PixelSnapshot], dest_stack: list[PixelSnapshot]) -> bool:
        if not source_stack:
            return False

        dest_stack.append(self.create_snapshot())
        self._pixels = list(source_stack.pop())
        return True

    def _draw_shape(
        self,
        pixels: list[ColorValue],
        shape_kind: ShapeKind,
        bounds: ShapeBounds,
        color: ColorValue,
    ) -> None:
        if shape_kind == "rect":
            self._draw_rect(pixels, bounds, color)
        else:
            self._draw_ellipse(pixels, bounds, color)

    def _draw_rect(self, pixels: list[ColorValue], bounds: ShapeBounds, color: ColorValue) -> None:
        left, top, width, height = bounds
        right = left + width - 1
        bottom = top + height - 1

        for col in range(left, right + 1):
            self._set_pixel(pixels, col, top, color)
            self._set_pixel(pixels, col, bottom, color)
        for row in range(top, bottom + 1):
            self._set_pixel(pixels, left, row, color)
            self._set_pixel(pixels, right, row, color)

    def _draw_ellipse(self, pixels: list[ColorValue], bounds: ShapeBounds, color: ColorValue) -> None:
        left, top, width, height = bounds
        if width <= 2 or height <= 2:
            self._draw_rect(pixels, bounds, color)
            return

        radius_x = (width - 1) / 2
        radius_y = (height - 1) / 2
        center_x = left + radius_x
        center_y = top + radius_y
        steps = max(12, int(2 * pi * max(radius_x, radius_y) * 2))

        for step in range(steps):
            angle = 2 * pi * step / steps
            col = round(center_x + radius_x * cos(angle))
            row = round(center_y + radius_y * sin(angle))
            self._set_pixel(pixels, col, row, color)

    def _set_pixel(self, pixels: list[ColorValue], col: int, row: int, color: ColorValue) -> None:
        if self.contains(col, row):
            pixels[self._pixel_index(col, row)] = color

    def _pixel_index(self, col: int, row: int) -> int:
        return row * self.columns + col
