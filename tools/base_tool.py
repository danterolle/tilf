from abc import ABC, abstractmethod
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent, QPainter, QCursor

from state import AppState
from ui.canvas import Canvas


class BaseTool(ABC):
    def __init__(self, canvas: Canvas, app_state: AppState):
        self.canvas = canvas
        self.app_state = app_state

    @abstractmethod
    def mousePressEvent(self, event: QMouseEvent, cell: QPoint) -> None:
        pass

    @abstractmethod
    def mouseMoveEvent(self, event: QMouseEvent, cell: QPoint) -> None:
        pass

    @abstractmethod
    def mouseReleaseEvent(self, event: QMouseEvent, cell: QPoint) -> None:
        pass

    def paint(self, painter: QPainter) -> None:
        """
        Optional: for tools that need a preview overlay (e.g., shapes).
        """
        pass

    def get_cursor(self) -> QCursor:
        return QCursor(Qt.CursorShape.CrossCursor)