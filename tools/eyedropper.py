from PySide6.QtCore import QPoint
from PySide6.QtGui import QMouseEvent, QColor
from tools.base_tool import BaseTool
from utils import config


class Eyedropper(BaseTool):
    def mousePressEvent(self, event: QMouseEvent, cell: QPoint):
        color = QColor(self.canvas.image.pixel(cell))
        self.app_state.set_primary_color(color)
        # Switch back to the pencil tool for a better workflow
        self.app_state.set_tool(config.ToolType.PENCIL)

    def mouseMoveEvent(self, event: QMouseEvent, cell: QPoint):
        pass

    def mouseReleaseEvent(self, event: QMouseEvent, cell: QPoint):
        pass