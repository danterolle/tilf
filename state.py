from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor
from utils import config


class AppState(QObject):
    dirty_changed = Signal(bool)
    file_path_changed = Signal(str)
    primary_color_changed = Signal(QColor)
    secondary_color_changed = Signal(QColor)
    tool_changed = Signal(str)
    image_changed = Signal()

    def __init__(self):
        super().__init__()
        self._is_dirty: bool = False
        self._current_file_path: Optional[str] = None
        self._primary_color: QColor = config.DEFAULT_PRIMARY_COLOR
        self._secondary_color: QColor = config.DEFAULT_SECONDARY_COLOR
        self._current_tool: str = "pencil"

    @property
    def is_dirty(self) -> bool:
        return self._is_dirty

    def set_dirty(self, dirty: bool):
        if self._is_dirty != dirty:
            self._is_dirty = dirty
            self.dirty_changed.emit(dirty)

    @property
    def current_file_path(self) -> Optional[str]:
        return self._current_file_path

    def set_file_path(self, path: Optional[str], mark_dirty: bool = False):
        self._current_file_path = path
        self.set_dirty(mark_dirty)
        self.file_path_changed.emit(path or "Untitled")

    @property
    def primary_color(self) -> QColor:
        return self._primary_color

    def set_primary_color(self, color: QColor):
        if color.isValid() and self._primary_color != color:
            self._primary_color = color
            self.primary_color_changed.emit(color)

    @property
    def secondary_color(self) -> QColor:
        return self._secondary_color

    def set_secondary_color(self, color: QColor):
        if color.isValid() and self._secondary_color != color:
            self._secondary_color = color
            self.secondary_color_changed.emit(color)

    @property
    def current_tool(self) -> str:
        return self._current_tool

    def set_tool(self, tool_name: str):
        if self._current_tool != tool_name and tool_name in config.TOOLS:
            self._current_tool = tool_name
            self.tool_changed.emit(tool_name)

    def notify_image_changed(self):
        self.set_dirty(True)
        self.image_changed.emit()