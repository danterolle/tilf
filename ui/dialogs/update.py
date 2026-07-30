from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from utils import config
from utils.update_checker import UpdateStatus


class UpdateDialog(QDialog):
    def __init__(self, parent: QWidget | None, status: UpdateStatus | None = None, error: str | None = None) -> None:
        super().__init__(parent)
        self._release_url = status.release_url if status else config.RELEASES_URL

        title, message = self._copy_for(status, error)
        self.setWindowTitle(config.TITLE_CHECK_UPDATES)
        self.setMinimumWidth(430)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)

        card = QFrame()
        card.setObjectName("updateCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("updateTitle")

        message_label = QLabel(message)
        message_label.setObjectName("updateMessage")
        message_label.setWordWrap(True)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        if status is None or status.is_update_available:
            release_button = QPushButton(config.BTN_OPEN_RELEASES)
            release_button.setProperty("variant", "primary")
            release_button.clicked.connect(self._open_release_page)
            button_layout.addWidget(release_button)

        ok_button = QPushButton(config.BTN_OK)
        ok_button.setProperty("variant", "secondary")
        ok_button.setDefault(True)
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        card_layout.addWidget(title_label)
        card_layout.addWidget(message_label)
        card_layout.addLayout(button_layout)
        layout.addWidget(card)

    def _copy_for(self, status: UpdateStatus | None, error: str | None) -> tuple[str, str]:
        if error is not None:
            return config.TITLE_UPDATE_CHECK_FAILED, config.MSG_UPDATE_CHECK_FAILED_FMT.format(error=error)
        if status is None:
            return config.TITLE_UPDATE_CHECK_FAILED, config.MSG_UPDATE_CHECK_FAILED_FMT.format(error="unknown error")
        if status.is_update_available:
            return (
                config.TITLE_UPDATE_AVAILABLE,
                config.MSG_UPDATE_AVAILABLE_FMT.format(
                    latest_version=status.latest_version,
                    current_version=status.current_version,
                ),
            )
        return (
            config.TITLE_UPDATE_CURRENT,
            config.MSG_UPDATE_CURRENT_FMT.format(current_version=status.current_version),
        )

    def _open_release_page(self) -> None:
        QDesktopServices.openUrl(QUrl(self._release_url))
        self.accept()
