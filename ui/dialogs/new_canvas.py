from typing import Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QSpinBox, QPushButton, QHBoxLayout, QWidget
)
from utils import config


class NewCanvas(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle(config.TITLE_NEW_CANVAS)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
        layout = QFormLayout(self)

        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 1024)
        self.width_spinbox.setValue(16)
        layout.addRow(config.LABEL_WIDTH, self.width_spinbox)

        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(1, 1024)
        self.height_spinbox.setValue(16)
        layout.addRow(config.LABEL_HEIGHT, self.height_spinbox)

        ok_button = QPushButton(config.BTN_OK)
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton(config.BTN_CANCEL)
        cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

    def get_size(self) -> Tuple[int, int]:
        return self.width_spinbox.value(), self.height_spinbox.value()