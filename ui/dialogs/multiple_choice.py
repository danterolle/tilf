from typing import List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QWidget, QRadioButton, QDialogButtonBox
)


class MultipleChoice(QDialog):
    def __init__(self, title: str, question: str, options: List[str], parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.question = question
        self.options = options
        self.option_group = []
        self.selected_option = None
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

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )  # type: ignore
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def _update_selected_option(self) -> None:
        self.selected_option = None
        for radio_button in self.option_group:
            if radio_button.isChecked():
                self.selected_option = radio_button.text()
                break

    def get_selected_option(self) -> str | None:
        return self.selected_option