from collections.abc import Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

Choice = tuple[str, str, str]


class ConfirmDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        choices: Sequence[Choice],
        parent: QWidget | None = None,
        default_value: str | None = None,
    ) -> None:
        super().__init__(parent)
        self._selected_value: str | None = None

        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(380)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 18, 18, 18)

        card = QFrame()
        card.setObjectName("confirmCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(12)

        accent = QFrame()
        accent.setObjectName("confirmAccent")
        accent.setFixedHeight(4)

        title_label = QLabel(title)
        title_label.setObjectName("confirmTitle")

        message_label = QLabel(message)
        message_label.setObjectName("confirmMessage")
        message_label.setWordWrap(True)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addStretch()

        for label, value, variant in choices:
            button = QPushButton(label)
            button.setProperty("variant", variant)
            button.clicked.connect(lambda checked=False, selected=value: self._select(selected))
            if value == default_value:
                button.setDefault(True)
            button_layout.addWidget(button)

        card_layout.addWidget(accent)
        card_layout.addWidget(title_label)
        card_layout.addWidget(message_label)
        card_layout.addLayout(button_layout)
        root_layout.addWidget(card)

    @property
    def selected_value(self) -> str | None:
        return self._selected_value

    def _select(self, value: str) -> None:
        self._selected_value = value
        self.accept()


def ask_confirmation(
    parent: QWidget,
    title: str,
    message: str,
    confirm_text: str,
    cancel_text: str,
    *,
    default_confirm: bool = False,
    destructive: bool = False,
) -> bool:
    confirm_variant = "danger" if destructive else "primary"
    default_value = "confirm" if default_confirm else "cancel"
    dialog = ConfirmDialog(
        title,
        message,
        (
            (cancel_text, "cancel", "secondary"),
            (confirm_text, "confirm", confirm_variant),
        ),
        parent,
        default_value,
    )
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return False
    return dialog.selected_value == "confirm"


def ask_choice(
    parent: QWidget,
    title: str,
    message: str,
    choices: Sequence[Choice],
    default_value: str,
) -> str | None:
    dialog = ConfirmDialog(title, message, choices, parent, default_value)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialog.selected_value
