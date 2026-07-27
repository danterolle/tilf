from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QWidget,
)

from utils import config


class NewCanvas(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(config.TITLE_NEW_CANVAS)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
        layout = QFormLayout(self)

        self.preset_combo = QComboBox()
        for preset_name in config.CANVAS_PRESETS:
            self.preset_combo.addItem(preset_name)
        layout.addRow(config.LABEL_PRESET, self.preset_combo)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(config.MIN_CANVAS_SIZE, config.MAX_CANVAS_SIZE)
        self.width_spin.setValue(config.DEFAULT_WIDTH)
        self.width_spin.setSuffix(" px")
        layout.addRow(config.LABEL_WIDTH, self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(config.MIN_CANVAS_SIZE, config.MAX_CANVAS_SIZE)
        self.height_spin.setValue(config.DEFAULT_HEIGHT)
        self.height_spin.setSuffix(" px")
        layout.addRow(config.LABEL_HEIGHT, self.height_spin)

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, config.MAX_TILE_COLS)
        self.cols_spin.setValue(config.DEFAULT_TILE_COLS)
        layout.addRow(config.LABEL_TILE_COLUMNS, self.cols_spin)

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, config.MAX_TILE_ROWS)
        self.rows_spin.setValue(config.DEFAULT_TILE_ROWS)
        layout.addRow(config.LABEL_TILE_ROWS, self.rows_spin)

        self.tile_size_spin = QSpinBox()
        self.tile_size_spin.setRange(config.MIN_TILE_SIZE, config.MAX_TILE_SIZE)
        self.tile_size_spin.setSingleStep(8)
        self.tile_size_spin.setValue(config.DEFAULT_TILE_SIZE)
        self.tile_size_spin.setSuffix(" px")
        layout.addRow(config.LABEL_TILE_SIZE, self.tile_size_spin)

        self.canvas_size_label = QLabel()
        layout.addRow(config.LABEL_RESULTING_CANVAS, self.canvas_size_label)

        self.preset_combo.currentTextChanged.connect(self._apply_preset)
        self.width_spin.valueChanged.connect(self._sync_tile_fields_from_size)
        self.height_spin.valueChanged.connect(self._sync_tile_fields_from_size)
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

    def _apply_preset(self, preset_name: str) -> None:
        width, height = config.CANVAS_PRESETS[preset_name]
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
        self._sync_tile_fields_from_size()

    def _sync_tile_fields_from_size(self) -> None:
        tile_size = self.tile_size_spin.value()
        self.cols_spin.blockSignals(True)
        self.rows_spin.blockSignals(True)
        self.cols_spin.setValue(max(1, self.width_spin.value() // tile_size))
        self.rows_spin.setValue(max(1, self.height_spin.value() // tile_size))
        self.cols_spin.blockSignals(False)
        self.rows_spin.blockSignals(False)
        self._update_canvas_size()

    def _update_canvas_size(self) -> None:
        tile_width = self.cols_spin.value() * self.tile_size_spin.value()
        tile_height = self.rows_spin.value() * self.tile_size_spin.value()
        self.canvas_size_label.setText(
            f"{self.width_spin.value()} x {self.height_spin.value()} px"
            f" ({tile_width} x {tile_height} tile grid)"
        )

    def get_size(self) -> tuple[int, int, int, int, int]:
        return (
            self.width_spin.value(),
            self.height_spin.value(),
            self.cols_spin.value(),
            self.rows_spin.value(),
            self.tile_size_spin.value(),
        )
