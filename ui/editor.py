import os
from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QColor, QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QDockWidget,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from file_manager import FileManager
from state import AppState
from ui.canvas import Canvas
from ui.dialogs.about import About
from ui.dialogs.multiple_choice import MultipleChoice
from ui.toolbar import Toolbar
from ui.widgets.color_swatch import ColorSwatchButton
from utils import config


class TilfEditor(QMainWindow):
    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state

        self.setWindowTitle(config.APP_NAME)
        self.resize(1280, 720)
        self.setAcceptDrops(True)

        self.canvas = Canvas(self.app_state)
        self.file_manager = FileManager(self, self.app_state, self.canvas)
        self._preview_dirty = False

        self._setup_central_widget()
        self._setup_status_bar()
        self._setup_menu_bar()
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

        reset_button = QPushButton(config.BTN_RESET_ZOOM)
        reset_button.setFixedWidth(100)
        reset_button.setToolTip(config.RESET_ZOOM_TOOLTIP_FMT.format(zoom=config.DEFAULT_ZOOM))

        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(reset_button)
        self.status_bar.addPermanentWidget(zoom_widget)

        self.zoom_slider.valueChanged.connect(self.canvas.set_cell_size)
        self.canvas.zoom_changed.connect(self.zoom_slider.setValue)
        reset_button.clicked.connect(lambda: self.canvas.set_cell_size(config.DEFAULT_ZOOM))

    def _setup_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu(config.MENU_FILE)
        file_menu.addAction(config.ACTION_NEW, self.file_manager.new_file, "Ctrl+N")
        file_menu.addAction(config.ACTION_OPEN, self.file_manager.open_file, "Ctrl+O")
        file_menu.addAction(config.ACTION_SAVE, self.save_file, "Ctrl+S")
        file_menu.addSeparator()
        file_menu.addAction(config.ACTION_QUIT, QApplication.quit, "Ctrl+Q")

        edit_menu = menu_bar.addMenu(config.MENU_EDIT)
        self.undo_menu_action = edit_menu.addAction(config.ACTION_UNDO, self.canvas.undo, "Ctrl+Z")
        self.redo_menu_action = edit_menu.addAction(config.ACTION_REDO, self.canvas.redo, "Ctrl+Y")
        edit_menu.addSeparator()
        edit_menu.addAction(config.ACTION_CLEAR_CANVAS, self.clear_canvas)

        view_menu = menu_bar.addMenu(config.MENU_VIEW)
        view_menu.addAction(config.ACTION_RESET_ZOOM, lambda: self.canvas.set_cell_size(config.DEFAULT_ZOOM))
        view_menu.addAction(config.ACTION_GRID_COLOR, self.choose_grid_color)

        help_menu = menu_bar.addMenu(config.MENU_HELP)
        help_menu.addAction(config.ACTION_ABOUT, self.about)

    def _setup_toolbar(self) -> None:
        handlers: dict[str, Callable[..., object]] = {
            "new_file": self.file_manager.new_file,
            "open_file": self.file_manager.open_file,
            "save_file": self.save_file,
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
        self.toolbar_builder = Toolbar(self, self.app_state, handlers)
        self.addToolBar(self.toolbar_builder.create_toolbar())
        self.undo_toolbar_action = self.toolbar_builder.action_for_handler("undo")
        self.redo_toolbar_action = self.toolbar_builder.action_for_handler("redo")

    def _setup_preview_dock(self) -> None:
        self.primary_color_button = ColorSwatchButton()
        self.primary_color_button.clicked.connect(self.choose_primary_color)
        self.secondary_color_button = ColorSwatchButton()
        self.secondary_color_button.clicked.connect(self.choose_secondary_color)
        self.canvas_info_label = QLabel()
        self.zoom_value_label = QLabel()

        self.preview_label = QLabel()
        self.preview_label.setObjectName("previewLabel")
        self.preview_label.setMinimumSize(150, 150)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container = QWidget()
        container.setObjectName("inspectorPanel")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        layout.addWidget(self._create_preview_group())
        layout.addWidget(self._create_color_group())
        layout.addWidget(self._create_canvas_group())
        layout.addStretch()

        dock = QDockWidget(config.LABEL_INSPECTOR, self)
        dock.setWidget(container)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self._update_color_swatch(self.primary_color_button, self.app_state.primary_color)
        self._update_color_swatch(self.secondary_color_button, self.app_state.secondary_color)
        self._update_canvas_info()
        self._update_zoom_label(self.canvas.cell_size)

    def _create_preview_group(self) -> QGroupBox:
        group = QGroupBox(config.LABEL_PREVIEW)
        layout = QVBoxLayout(group)
        layout.addWidget(self.preview_label)
        return group

    def _create_color_group(self) -> QGroupBox:
        group = QGroupBox(config.LABEL_COLORS)
        layout = QFormLayout(group)
        layout.addRow(config.LABEL_PRIMARY_COLOR, self.primary_color_button)
        layout.addRow(config.LABEL_BACKGROUND_COLOR, self.secondary_color_button)
        return group

    def _create_canvas_group(self) -> QGroupBox:
        group = QGroupBox(config.LABEL_CANVAS)
        layout = QFormLayout(group)
        grid_color_button = QPushButton(config.BTN_GRID_COLOR)
        grid_color_button.clicked.connect(self.choose_grid_color)
        layout.addRow(config.LABEL_CANVAS_SIZE, self.canvas_info_label)
        layout.addRow(config.LABEL_ZOOM, self.zoom_value_label)
        layout.addRow(config.LABEL_GRID, grid_color_button)
        return group

    def _connect_signals(self) -> None:
        self.app_state.dirty_changed.connect(self._update_window_title)
        self.app_state.file_path_changed.connect(self._update_window_title)
        self.app_state.image_changed.connect(self._schedule_preview_refresh)
        self.app_state.image_changed.connect(self._update_canvas_info)
        self.app_state.primary_color_changed.connect(
            lambda color: self._update_color_swatch(self.primary_color_button, color)
        )
        self.app_state.secondary_color_changed.connect(
            lambda color: self._update_color_swatch(self.secondary_color_button, color)
        )

        self.canvas.pixel_hovered.connect(self._update_status_bar)
        self.canvas.zoom_changed.connect(self._update_zoom_label)
        self.canvas.history_changed.connect(self._update_history_actions)
        self.canvas.zoom_changed.connect(
            lambda z: self.status_bar.showMessage(
                f"Zoom: {z}x",
                1500
            )
        )
        self._update_history_actions(self.canvas.document.can_undo, self.canvas.document.can_redo)

    def choose_primary_color(self) -> None:
        color = QColorDialog.getColor(self.app_state.primary_color, self, config.TITLE_PRIMARY_COLOR)
        if color.isValid():
            self.app_state.set_primary_color(color)

    def choose_secondary_color(self) -> None:
        color = QColorDialog.getColor(
            self.app_state.secondary_color, self, config.TITLE_SECONDARY_COLOR,
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )
        if color.isValid():
            self.app_state.set_secondary_color(color)

    def choose_grid_color(self) -> None:
        color = QColorDialog.getColor(self.canvas.grid_color, self, config.TITLE_GRID_COLOR)
        if color.isValid():
            self.canvas.grid_color = color
            self.canvas.update()

    def clear_canvas(self) -> None:
        reply = QMessageBox.question(
            self, config.TITLE_CLEAR_CANVAS, config.MSG_CLEAR_CONFIRM,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            return self.canvas.clear_canvas()
        return None

    def save_file(self) -> bool:
        saved = self.file_manager.save_file()
        if saved:
            self.status_bar.showMessage(config.MSG_FILE_SAVED, 2000)
        return saved

    def toggle_grid(self, checked: bool) -> None:
        self.canvas.is_grid_visible = checked
        self.canvas.update()

    def shift_canvas(self) -> None:
        dialog = MultipleChoice(config.TITLE_SHIFT_CANVAS, config.MSG_SHIFT_CANVAS, config.SHIFT_OPTIONS, self)
        if dialog.exec():
            selected = dialog.get_selected_option()
            if selected:
                self.canvas.shift_image(selected.lower())

    def about(self) -> int:
        return About(self).exec()

    def _update_window_title(self) -> None:
        filename = os.path.basename(
            self.app_state.current_file_path) if self.app_state.current_file_path else config.UNTITLED_NAME
        dirty_marker = config.DIRTY_MARKER if self.app_state.is_dirty else ""
        return self.setWindowTitle(config.WINDOW_TITLE_FMT.format(marker=dirty_marker, name=filename))

    def _update_status_bar(self, col: int, row: int, color: QColor) -> None:
        try:
            self.status_bar.showMessage(f"x={col}, y={row} | color={color.name(QColor.NameFormat.HexArgb)}")
        except RuntimeError:
            pass

    def _schedule_preview_refresh(self) -> None:
        if not self._preview_dirty:
            self._preview_dirty = True
            QTimer.singleShot(50, self._refresh_preview)

    def _update_canvas_info(self) -> None:
        self.canvas_info_label.setText(f"{self.canvas.columns} x {self.canvas.rows}px")

    def _update_zoom_label(self, zoom: int) -> None:
        self.zoom_value_label.setText(f"{zoom}x")

    def _update_color_swatch(self, button: ColorSwatchButton, color: QColor) -> None:
        button.set_color(color)

    def _update_history_actions(self, can_undo: bool, can_redo: bool) -> None:
        if self.undo_menu_action is not None:
            self.undo_menu_action.setEnabled(can_undo)
        if self.redo_menu_action is not None:
            self.redo_menu_action.setEnabled(can_redo)
        if self.undo_toolbar_action is not None:
            self.undo_toolbar_action.setEnabled(can_undo)
        if self.redo_toolbar_action is not None:
            self.redo_toolbar_action.setEnabled(can_redo)

    def _refresh_preview(self) -> None:
        self._preview_dirty = False
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
            u.isLocalFile() and u.toLocalFile().lower().endswith(config.SUPPORTED_EXTENSIONS)
            for u in mime_data.urls()
        ):
            return event.acceptProposedAction()
        return None

    def dropEvent(self, event: QDropEvent) -> None:
        url = next(
            (
                u for u in event.mimeData().urls()
                if u.isLocalFile() and u.toLocalFile().lower().endswith(config.SUPPORTED_EXTENSIONS)
            ),
            None,
        )
        if url:
            self.file_manager.open_file(path=url.toLocalFile())
            return event.acceptProposedAction()
        return None

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.app_state.is_dirty:
            # Create a recovery copy before asking, so Cancel also preserves unsaved work.
            self.file_manager.autosave_on_exit()

            reply = QMessageBox.question(
                self, config.TITLE_UNSAVED, config.MSG_SAVE_BEFORE_QUIT,
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
                return event.accept()
        else:
            return event.accept()
