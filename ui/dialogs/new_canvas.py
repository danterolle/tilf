from typing import Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QSpinBox, QPushButton, QHBoxLayout, QWidget
)


class NewCanvas(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("New Canvas")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
        layout = QFormLayout(self)

        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 1024)
        self.width_spinbox.setValue(16)
        layout.addRow("Width (px):", self.width_spinbox)

        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(1, 1024)
        self.height_spinbox.setValue(16)
        layout.addRow("Height (px):", self.height_spinbox)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

    def get_size(self) -> Tuple[int, int]:
        return self.width_spinbox.value(), self.height_spinbox.value()