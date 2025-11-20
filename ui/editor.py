import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QPixmap, QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QStatusBar, QColorDialog,
    QScrollArea, QMessageBox, QLabel, QSlider,
    QHBoxLayout, QDockWidget, QVBoxLayout, QPushButton
)
from state import AppState
from utils import config
from file_manager import FileManager
from ui.canvas import Canvas
from ui.toolbar import Toolbar
from ui.dialogs.about import About
from ui.dialogs.multiple_choice import MultipleChoice


class TilfEditor(QMainWindow):
    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state

        self.setWindowTitle(config.APP_NAME)
        self.resize(1280, 720)
        self.setAcceptDrops(True)

        self.canvas = Canvas(self.app_state)
        self.file_manager = FileManager(self, self.app_state, self.canvas)

        self._setup_central_widget()
        self._setup_status_bar()
        self._setup_toolbar()
        self._setup_preview_dock()
        self._connect_signals()

        self.app_state.set_file_path(None)
        self.app_state.set_tool(config.ToolType.PENCIL)

    def _setup_central_widget(self) -> None:
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setWidget(self.canvas)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setCentralWidget(scroll_area)

    def _setup_status_bar(self) -> None:
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        zoom_widget = QWidget()
        zoom_layout = QHBoxLayout(zoom_widget)
        zoom_layout.setContentsMargins(0, 0, 8, 0)
        zoom_layout.setSpacing(5)

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(1)
        self.zoom_slider.setMaximum(50)
        self.zoom_slider.setValue(config.DEFAULT_ZOOM)
        self.zoom_slider.setFixedWidth(150)

        reset_button = QPushButton("Reset Zoom")
        reset_button.setFixedWidth(100)
        reset_button.setToolTip(f"Reset zoom to {config.DEFAULT_ZOOM}x")

        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(reset_button)
        self.status_bar.addPermanentWidget(zoom_widget)

        self.zoom_slider.valueChanged.connect(self.canvas.set_cell_size)
        self.canvas.zoom_changed.connect(self.zoom_slider.setValue)
        reset_button.clicked.connect(lambda: self.canvas.set_cell_size(config.DEFAULT_ZOOM))

    def _setup_toolbar(self) -> None:
        handlers = {
            "new_file": self.file_manager.new_file,
            "open_file": self.file_manager.open_file,
            "save_file": self.file_manager.save_file,
            "undo": self.canvas.undo,
            "redo": self.canvas.redo,
            "choose_primary_color": self.choose_primary_color,
            "choose_secondary_color": self.choose_secondary_color,
            "clear_canvas": self.clear_canvas,
            "toggle_grid": self.toggle_grid,
            "choose_grid_color": self.choose_grid_color,
            "shift_canvas": self.shift_canvas,
            "about": self.about,
        }
        builder = Toolbar(self, self.app_state, handlers)
        self.addToolBar(builder.create_toolbar())

    def _setup_preview_dock(self) -> None:
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(150, 150)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background:#1e1e1e; border:1px solid #444; border-radius:8px;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        label = QLabel("Preview")
        label.setStyleSheet("font-weight:bold; color:#ddd;")
        layout.addWidget(label)
        layout.addWidget(self.preview_label, 1)

        dock = QDockWidget("Preview", self)
        dock.setWidget(container)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _connect_signals(self) -> None:
        self.app_state.dirty_changed.connect(self._update_window_title)
        self.app_state.file_path_changed.connect(self._update_window_title)
        self.app_state.image_changed.connect(self._refresh_preview)

        self.canvas.pixel_hovered.connect(self._update_status_bar)
        self.canvas.zoom_changed.connect(
            lambda z: self.status_bar.showMessage(
                f"Zoom: {z}x",
                1500
            )
        )

    def choose_primary_color(self) -> None:
        color = QColorDialog.getColor(self.app_state.primary_color, self, "Choose Primary Color")
        if color.isValid(): self.app_state.set_primary_color(color)

    def choose_secondary_color(self) -> None:
        color = QColorDialog.getColor(
            self.app_state.secondary_color, self, "Choose Secondary Color",
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )
        if color.isValid(): self.app_state.set_secondary_color(color)

    def choose_grid_color(self) -> None:
        color = QColorDialog.getColor(self.canvas.grid_color, self, "Choose Grid Color")
        if color.isValid():
            self.canvas.grid_color = color
            self.canvas.update()

    def clear_canvas(self) -> None:
        reply = QMessageBox.question(
            self, "Clear Canvas", "Are you sure you want to clear the canvas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            return self.canvas.clear_canvas()
        return None

    def toggle_grid(self, checked: bool) -> None:
        self.canvas.is_grid_visible = checked
        self.canvas.update()

    def shift_canvas(self) -> None:
        options = ["Left", "Right", "Up", "Down"]
        dialog = MultipleChoice("Shift Canvas", "Shift canvas 1px to the:", options, self)
        if dialog.exec():
            selected = dialog.get_selected_option()
            if selected:
                self.canvas.shift_image(selected.lower())

    def about(self) -> int:
        return About(self).exec()

    def _update_window_title(self) -> None:
        filename = os.path.basename(
            self.app_state.current_file_path) if self.app_state.current_file_path else "Untitled"
        dirty_marker = "*" if self.app_state.is_dirty else ""
        return self.setWindowTitle(f"{dirty_marker}{filename} - {config.APP_NAME}")

    def _update_status_bar(self, col: int, row: int, color: QColor) -> None:
        try:
            self.status_bar.showMessage(f"x={col}, y={row} | color={color.name(QColor.NameFormat.HexArgb)}")
        except RuntimeError:
            pass

    def _refresh_preview(self) -> None:
        if self.canvas.image.isNull():
            return None
        pixmap = QPixmap.fromImage(self.canvas.image)
        scaled_pixmap = pixmap.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )
        return self.preview_label.setPixmap(scaled_pixmap)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        mime_data = event.mimeData()
        if mime_data.hasUrls() and any(
                u.isLocalFile() and u.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
                for u in mime_data.urls()):
            return event.acceptProposedAction()
        return None

    def dropEvent(self, event: QDropEvent) -> None:
        url = next((u for u in event.mimeData().urls() if u.isLocalFile()), None)
        if url:
            self.file_manager.open_file(path=url.toLocalFile())
            return event.acceptProposedAction()
        return None

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.app_state.is_dirty:
            # Perform the autosave as the very first step
            # as soon as the user attempts to close the window with unsaved changes.
            self.file_manager.autosave_on_exit()

            reply = QMessageBox.question(
                self, "Unsaved Changes", "You have unsaved changes. Do you want to save before quitting?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                if self.file_manager.save_file():
                    return event.accept()
                else:
                    return event.ignore()
            elif reply == QMessageBox.StandardButton.Cancel:
                return event.ignore()
            else:
                self.file_manager.autosave_on_exit()
                return event.accept()
        else:
            return event.accept()