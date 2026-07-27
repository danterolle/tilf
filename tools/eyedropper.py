from PySide6.QtCore import QPoint
from PySide6.QtGui import QMouseEvent

from tools.base_tool import BaseTool
from utils import config


class Eyedropper(BaseTool):
    def mousePressEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        color = self.canvas.pixel_color(cell.x(), cell.y())
        self.app_state.set_primary_color(color)
        self.app_state.set_tool(config.ToolType.PENCIL)
        return False

    def mouseMoveEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        return False

    def mouseReleaseEvent(self, event: QMouseEvent, cell: QPoint) -> bool:
        return False
