import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from utils import config
from utils.resource_path import get_resource_path


class About(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(config.TITLE_ABOUT)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(0)

        card = QFrame()
        card.setObjectName("aboutCard")
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setContentsMargins(24, 24, 24, 20)
        card_layout.setSpacing(12)

        icon_path = get_resource_path(config.LOGO_RESOURCE)
        icon_label = QLabel()

        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            icon_label.setPixmap(
                pixmap.scaled(
                    112,
                    112,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            icon_label.setObjectName("missingIconLabel")
            icon_label.setText("(Icon)")
            icon_label.setFixedSize(128, 128)

        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("Tilf")
        title_label.setObjectName("aboutTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version_label = QLabel(f"v{config.APP_VERSION} · GPL v3")
        version_label.setObjectName("aboutVersion")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        description_label = QLabel(
            "Tiny Elf is a focused pixel art editor for sprites, icons and compact 2D assets."
        )
        description_label.setObjectName("aboutDescription")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setWordWrap(True)

        author_label = QLabel("Created by Dario 'danterolle' Camonita")
        author_label.setObjectName("aboutMeta")
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addStretch()

        github_button = QPushButton(config.BTN_GITHUB)
        github_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(config.PROJECT_URL)))
        email_button = QPushButton(config.BTN_EMAIL)
        email_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(config.PROJECT_EMAIL_URL)))

        button_layout.addWidget(github_button)
        button_layout.addWidget(email_button)
        button_layout.addStretch()

        card_layout.addWidget(icon_label)
        card_layout.addWidget(title_label)
        card_layout.addWidget(version_label)
        card_layout.addWidget(description_label)
        card_layout.addWidget(author_label)
        card_layout.addLayout(button_layout)
        layout.addWidget(card)
