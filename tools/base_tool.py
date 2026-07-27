from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QCursor, QMouseEvent, QPainter

from state import AppState

if TYPE_CHECKING:
    from ui.canvas import Canvas


class BaseTool(ABC):
    is_drag_tool = False

    def __init__(self, canvas: Canvas, app_state: AppState) -> None:
        self.canvas = canvas
        self.app_state = app_state

    @abstractmethod
    def mousePressEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        return False

    @abstractmethod
    def mouseMoveEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        return False

    @abstractmethod
    def mouseReleaseEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        return False

    def paint(self, painter: QPainter) -> None:
        return None

    def get_cursor(self) -> QCursor:
        return QCursor(Qt.CursorShape.CrossCursor)
