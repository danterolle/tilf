from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QPushButton


class ColorSwatchButton(QPushButton):
    def __init__(self) -> None:
        super().__init__()
        self._color = QColor("transparent")
        self.setMinimumHeight(32)

    def set_color(self, color: QColor) -> None:
        self._color = QColor(color)
        color_name = self._color.name(QColor.NameFormat.HexArgb)
        self.setText(color_name)
        self.setToolTip(color_name)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        background_color = QColor(self._color)
        if not self.isEnabled():
            background_color.setAlpha(80)

        painter.setBrush(background_color)
        painter.setPen(QPen(QColor("#475569"), 1))
        painter.drawRoundedRect(rect, 8, 8)

        text_color = (
            QColor("#f8fafc")
            if self._color.lightness() < 150 or self._color.alpha() < 128
            else QColor("#111827")
        )
        painter.setPen(text_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
