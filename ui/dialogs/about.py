import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QLabel, QWidget
)
from config import resource_path

class About(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("About Tilf")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        icon_path = resource_path("assets/logo.png")
        icon_label = QLabel()

        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            icon_label.setPixmap(
                pixmap.scaled(
                    80,
                    80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            icon_label.setText("(Icon)")
            icon_label.setFixedSize(128, 128)
            icon_label.setStyleSheet("border: 1px dashed #888; color: #888; border-radius: 8px;")

        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_label = QLabel(
            "<br>Version 0.1 - under GPL v3 License<br>"
            "<br>Tilf (Tiny Elf) is a simple pixel art editor for creating, drawing and modifying images with "
            "pixel-level precision.<br>"
            "<br>It features essential tools like a pencil, fill bucket, and shapes, along with a grid system to "
            "easily create sprites and small tiles.<br>"
            "<br><a href="f'https://github.com/danterolle/tilf'">PRs are welcome.</a><br>"
            "<br>Thank you for using this tool!<br>"
            "<br>Created by Dario 'danterolle' Camonita<br>"
            "<br>Email: danterolle@catania.linux.it<br>"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setOpenExternalLinks(True)
        info_label.setWordWrap(True)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addStretch()

        layout.addWidget(icon_label)
        layout.addWidget(info_label)
        layout.addStretch()
        layout.addLayout(button_layout)