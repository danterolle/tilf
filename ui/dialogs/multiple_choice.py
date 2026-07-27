from collections.abc import Sequence

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


class MultipleChoice(QDialog):
    def __init__(self, title: str, question: str, options: Sequence[str], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.question = question
        self.options = options
        self.option_group: list[QRadioButton] = []
        self.selected_option: str | None = None
        self._create_option_selector()

    def _create_option_selector(self) -> None:
        layout = QVBoxLayout()
        question_label = QLabel(self.question)
        layout.addWidget(question_label)

        for option in self.options:
            radio_button = QRadioButton(option)
            radio_button.toggled.connect(self._update_selected_option)
            layout.addWidget(radio_button)
            self.option_group.append(radio_button)

        buttons = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        button_box = QDialogButtonBox(buttons)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def _update_selected_option(self, checked: bool = False) -> None:
        self.selected_option = None
        for radio_button in self.option_group:
            if radio_button.isChecked():
                self.selected_option = radio_button.text()
                break

    def get_selected_option(self) -> str | None:
        return self.selected_option
