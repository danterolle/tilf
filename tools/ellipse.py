from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter
from tools.shape import Shape

class Ellipse(Shape):
    def _draw_current_shape(self, painter: QPainter, rect: QRect):
        painter.drawEllipse(rect)
