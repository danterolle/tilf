from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtGui import QCursor, QMouseEvent
from PySide6.QtWidgets import QAbstractScrollArea, QWidget


class CanvasPanController(QObject):
    def __init__(self, scroll_area: QAbstractScrollArea, surface: QWidget) -> None:
        super().__init__(scroll_area)
        self._scroll_area = scroll_area
        self._surface = surface
        self._is_panning = False
        self._last_position: QPoint | None = None
        self._surface_cursor = surface.cursor()
        self._viewport_cursor = scroll_area.viewport().cursor()

        self._surface.installEventFilter(self)
        self._scroll_area.viewport().installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not isinstance(event, QMouseEvent):
            return super().eventFilter(watched, event)

        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.MiddleButton:
            self._start_panning(event)
            return True

        if event.type() == QEvent.Type.MouseMove and self._is_panning:
            self._pan_to(event)
            return True

        if (
            event.type() == QEvent.Type.MouseButtonRelease
            and event.button() == Qt.MouseButton.MiddleButton
            and self._is_panning
        ):
            self._stop_panning()
            return True

        return super().eventFilter(watched, event)

    def _start_panning(self, event: QMouseEvent) -> None:
        self._is_panning = True
        self._last_position = event.globalPosition().toPoint()
        self._surface_cursor = self._surface.cursor()
        self._viewport_cursor = self._scroll_area.viewport().cursor()
        pan_cursor = QCursor(Qt.CursorShape.ClosedHandCursor)
        self._surface.setCursor(pan_cursor)
        self._scroll_area.viewport().setCursor(pan_cursor)
        event.accept()

    def _pan_to(self, event: QMouseEvent) -> None:
        if self._last_position is None:
            return

        position = event.globalPosition().toPoint()
        delta = position - self._last_position
        self._last_position = position

        horizontal_scrollbar = self._scroll_area.horizontalScrollBar()
        vertical_scrollbar = self._scroll_area.verticalScrollBar()
        horizontal_scrollbar.setValue(horizontal_scrollbar.value() - delta.x())
        vertical_scrollbar.setValue(vertical_scrollbar.value() - delta.y())
        event.accept()

    def _stop_panning(self) -> None:
        self._is_panning = False
        self._last_position = None
        self._surface.setCursor(self._surface_cursor)
        self._scroll_area.viewport().setCursor(self._viewport_cursor)
