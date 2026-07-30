from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFormLayout, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ui.widgets.color_swatch import ColorSwatchButton
from utils import config

MAX_RECENT_COLORS = 6


class ColorPalette(QWidget):
    primary_color_requested = Signal()
    secondary_color_requested = Signal()
    recent_color_selected = Signal(QColor)
    reset_requested = Signal()
    swap_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._recent_colors: list[QColor] = []

        self.primary_button = ColorSwatchButton()
        self.primary_button.clicked.connect(lambda checked=False: self.primary_color_requested.emit())

        self.secondary_button = ColorSwatchButton()
        self.secondary_button.clicked.connect(lambda checked=False: self.secondary_color_requested.emit())

        self._recent_buttons = [ColorSwatchButton(show_text=False) for _ in range(MAX_RECENT_COLORS)]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addLayout(self._create_color_layout())
        layout.addLayout(self._create_action_layout())
        layout.addWidget(QLabel(config.LABEL_RECENT_COLORS))
        layout.addLayout(self._create_recent_layout())
        self._render_recent_colors()

    def set_primary_color(self, color: QColor) -> None:
        self.primary_button.set_color(color)

    def set_secondary_color(self, color: QColor) -> None:
        self.secondary_button.set_color(color)

    def remember_color(self, color: QColor) -> None:
        if not color.isValid():
            return

        color_key = color.name(QColor.NameFormat.HexArgb)
        self._recent_colors = [
            recent for recent in self._recent_colors
            if recent.name(QColor.NameFormat.HexArgb) != color_key
        ]
        self._recent_colors.insert(0, QColor(color))
        del self._recent_colors[MAX_RECENT_COLORS:]
        self._render_recent_colors()

    def _create_color_layout(self) -> QFormLayout:
        layout = QFormLayout()
        layout.addRow(config.LABEL_PRIMARY_COLOR, self.primary_button)
        layout.addRow(config.LABEL_BACKGROUND_COLOR, self.secondary_button)
        return layout

    def _create_action_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        swap_button = QPushButton(config.BTN_SWAP_COLORS)
        swap_button.clicked.connect(lambda checked=False: self.swap_requested.emit())
        reset_button = QPushButton(config.BTN_RESET_COLORS)
        reset_button.clicked.connect(lambda checked=False: self.reset_requested.emit())
        layout.addWidget(swap_button)
        layout.addWidget(reset_button)
        return layout

    def _create_recent_layout(self) -> QGridLayout:
        layout = QGridLayout()
        for index, button in enumerate(self._recent_buttons):
            button.setFixedSize(44, 34)
            button.clicked.connect(lambda checked=False, selected=index: self._select_recent_color(selected))
            layout.addWidget(button, index // 3, index % 3)
        return layout

    def _render_recent_colors(self) -> None:
        for index, button in enumerate(self._recent_buttons):
            if index < len(self._recent_colors):
                button.set_color(self._recent_colors[index])
                button.setVisible(True)
            else:
                button.setVisible(False)

    def _select_recent_color(self, index: int) -> None:
        if index < len(self._recent_colors):
            self.recent_color_selected.emit(QColor(self._recent_colors[index]))
