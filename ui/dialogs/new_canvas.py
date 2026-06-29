from typing import Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QSpinBox, QPushButton, QHBoxLayout, QLabel, QWidget
)
from utils import config


class NewCanvas(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle(config.TITLE_NEW_CANVAS)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
        layout = QFormLayout(self)

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, config.MAX_TILE_COLS)
        self.cols_spin.setValue(config.DEFAULT_TILE_COLS)
        layout.addRow("Columns:", self.cols_spin)

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, config.MAX_TILE_ROWS)
        self.rows_spin.setValue(config.DEFAULT_TILE_ROWS)
        layout.addRow("Rows:", self.rows_spin)

        self.tile_size_spin = QSpinBox()
        self.tile_size_spin.setRange(config.MIN_TILE_SIZE, config.MAX_TILE_SIZE)
        self.tile_size_spin.setSingleStep(8)
        self.tile_size_spin.setValue(config.DEFAULT_TILE_SIZE)
        layout.addRow("Tile size:", self.tile_size_spin)

        self.canvas_size_label = QLabel()
        layout.addRow("Canvas:", self.canvas_size_label)

        self.cols_spin.valueChanged.connect(self._update_canvas_size)
        self.rows_spin.valueChanged.connect(self._update_canvas_size)
        self.tile_size_spin.valueChanged.connect(self._update_canvas_size)
        self._update_canvas_size()

        ok_button = QPushButton(config.BTN_OK)
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton(config.BTN_CANCEL)
        cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

    def _update_canvas_size(self) -> None:
        width = self.cols_spin.value() * self.tile_size_spin.value()
        height = self.rows_spin.value() * self.tile_size_spin.value()
        self.canvas_size_label.setText(f"{width} \u00d7 {height} px")

    def get_size(self) -> Tuple[int, int, int, int, int]:
        cols = self.cols_spin.value()
        rows = self.rows_spin.value()
        tile_size = self.tile_size_spin.value()
        return (cols * tile_size, rows * tile_size, cols, rows, tile_size)