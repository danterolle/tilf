import os
from collections.abc import Callable

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QColor, QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QDockWidget,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
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
from ui.dialogs.confirm import ask_choice, ask_confirmation
from ui.dialogs.multiple_choice import MultipleChoice
from ui.dialogs.update import UpdateDialog
from ui.navigation import CanvasPanController
from ui.toolbar import Toolbar
from ui.widgets.color_palette import ColorPalette
from utils import config
from utils.log import get_logger
from utils.update_checker import UpdateCheckError, check_latest_release


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
        self._fit_zoom_active = False
        self._applying_fit_zoom = False

        self._setup_central_widget()
        self._setup_status_bar()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_preview_dock()
        self._connect_signals()

        self.app_state.set_file_path(None)
        self.app_state.set_tool(config.ToolType.PENCIL)
        QTimer.singleShot(0, self.file_manager.prompt_recover_autosave)

    def _setup_central_widget(self) -> None:
        self.canvas_scroll_area = QScrollArea()
        self.canvas_scroll_area.setWidgetResizable(False)
        self.canvas_scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas_scroll_area.setWidget(self.canvas)
        self.canvas_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.canvas_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.canvas_scroll_area.viewport().installEventFilter(self)
        self.pan_controller = CanvasPanController(self.canvas_scroll_area, self.canvas)
        self.setCentralWidget(self.canvas_scroll_area)

    def _setup_status_bar(self) -> None:
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        zoom_widget = QWidget()
        zoom_layout = QHBoxLayout(zoom_widget)
        zoom_layout.setContentsMargins(0, 0, 8, 0)
        zoom_layout.setSpacing(5)

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(config.MIN_ZOOM)
        self.zoom_slider.setMaximum(config.MAX_ZOOM)
        self.zoom_slider.setValue(config.DEFAULT_ZOOM)
        self.zoom_slider.setFixedWidth(150)

        self.zoom_preset_combo = QComboBox()
        self.zoom_preset_combo.setFixedWidth(105)
        self.zoom_preset_combo.addItem("Custom", None)
        self.zoom_preset_combo.addItem(config.ACTION_FIT_TO_WINDOW, "fit")
        for zoom in config.ZOOM_PRESETS:
            self.zoom_preset_combo.addItem(self._zoom_percent_label(zoom), zoom)

        reset_button = QPushButton(config.BTN_RESET_ZOOM)
        reset_button.setFixedWidth(100)
        reset_button.setToolTip(config.RESET_ZOOM_TOOLTIP_FMT.format(zoom=config.DEFAULT_ZOOM))

        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.zoom_preset_combo)
        zoom_layout.addWidget(reset_button)
        self.status_bar.addPermanentWidget(zoom_widget)

        self.zoom_slider.valueChanged.connect(self._set_zoom_from_slider)
        self.zoom_preset_combo.activated.connect(self._apply_zoom_combo_selection)
        reset_button.clicked.connect(self.reset_zoom)

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
        view_menu.addAction(config.ACTION_FIT_TO_WINDOW, self.fit_canvas_to_window, "Ctrl+0")
        view_menu.addAction(config.ACTION_ACTUAL_SIZE, self.set_actual_size, "Ctrl+1")
        view_menu.addAction(config.ACTION_ZOOM_IN, self.zoom_in, "Ctrl++")
        view_menu.addAction(config.ACTION_ZOOM_OUT, self.zoom_out, "Ctrl+-")
        view_menu.addAction(config.ACTION_RESET_ZOOM, self.reset_zoom)
        preset_menu = view_menu.addMenu(config.MENU_ZOOM_PRESETS)
        for zoom in config.ZOOM_PRESETS:
            preset_menu.addAction(
                self._zoom_percent_label(zoom),
                lambda checked=False, selected_zoom=zoom: self.set_zoom(selected_zoom),
            )
        view_menu.addSeparator()
        view_menu.addAction(config.ACTION_GRID_COLOR, self.choose_grid_color)

        help_menu = menu_bar.addMenu(config.MENU_HELP)
        help_menu.addAction(config.ACTION_CHECK_UPDATES, self.check_for_updates)
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
            "check_for_updates": self.check_for_updates,
            "about": self.about,
        }
        self.toolbar_builder = Toolbar(self, self.app_state, handlers)
        self.addToolBar(self.toolbar_builder.create_toolbar())
        self.undo_toolbar_action = self.toolbar_builder.action_for_handler("undo")
        self.redo_toolbar_action = self.toolbar_builder.action_for_handler("redo")

    def _setup_preview_dock(self) -> None:
        self.color_palette = ColorPalette()
        self.color_palette.primary_color_requested.connect(self.choose_primary_color)
        self.color_palette.secondary_color_requested.connect(self.choose_secondary_color)
        self.color_palette.recent_color_selected.connect(self.app_state.set_primary_color)
        self.color_palette.reset_requested.connect(self.reset_colors)
        self.color_palette.swap_requested.connect(self.swap_colors)
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

        inspector_area = QScrollArea()
        inspector_area.setWidgetResizable(True)
        inspector_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inspector_area.setWidget(container)

        dock = QDockWidget(config.LABEL_INSPECTOR, self)
        dock.setWidget(inspector_area)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self._on_primary_color_changed(self.app_state.primary_color)
        self._on_secondary_color_changed(self.app_state.secondary_color)
        self._update_canvas_info()
        self._sync_zoom_controls(self.canvas.cell_size)

    def _create_preview_group(self) -> QGroupBox:
        group = QGroupBox(config.LABEL_PREVIEW)
        layout = QVBoxLayout(group)
        layout.addWidget(self.preview_label)
        return group

    def _create_color_group(self) -> QGroupBox:
        group = QGroupBox(config.LABEL_COLORS)
        layout = QVBoxLayout(group)
        layout.addWidget(self.color_palette)
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
            self._on_primary_color_changed
        )
        self.app_state.secondary_color_changed.connect(
            self._on_secondary_color_changed
        )

        self.canvas.pixel_hovered.connect(self._update_status_bar)
        self.canvas.zoom_changed.connect(self._on_canvas_zoom_changed)
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

    def fit_canvas_to_window(self) -> None:
        viewport_size = self.canvas_scroll_area.viewport().size()
        width_zoom = max(config.MIN_ZOOM, (viewport_size.width() - 2) // max(1, self.canvas.columns))
        height_zoom = max(config.MIN_ZOOM, (viewport_size.height() - 2) // max(1, self.canvas.rows))
        self._fit_zoom_active = True
        self._applying_fit_zoom = True
        self.canvas.set_cell_size(min(config.MAX_ZOOM, width_zoom, height_zoom))
        self._applying_fit_zoom = False
        self._sync_zoom_controls(self.canvas.cell_size)

    def set_actual_size(self) -> None:
        self.set_zoom(config.MIN_ZOOM)

    def reset_zoom(self) -> None:
        self.set_zoom(config.DEFAULT_ZOOM)

    def set_zoom(self, zoom: int) -> None:
        self._fit_zoom_active = False
        self.canvas.set_cell_size(zoom)
        self._sync_zoom_controls(self.canvas.cell_size)

    def zoom_in(self) -> None:
        self.set_zoom(self.canvas.cell_size + 1)

    def zoom_out(self) -> None:
        self.set_zoom(self.canvas.cell_size - 1)

    def reset_colors(self) -> None:
        self.app_state.set_primary_color(config.DEFAULT_PRIMARY_COLOR)
        self.app_state.set_secondary_color(config.DEFAULT_SECONDARY_COLOR)

    def swap_colors(self) -> None:
        primary_color = QColor(self.app_state.primary_color)
        secondary_color = QColor(self.app_state.secondary_color)
        self.app_state.set_primary_color(secondary_color)
        self.app_state.set_secondary_color(primary_color)

    def clear_canvas(self) -> None:
        should_clear = ask_confirmation(
            self, config.TITLE_CLEAR_CANVAS, config.MSG_CLEAR_CONFIRM,
            config.BTN_CLEAR,
            config.BTN_CANCEL,
            destructive=True,
        )
        if should_clear:
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

    def check_for_updates(self) -> int:
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            update_status = check_latest_release()
        except UpdateCheckError as error:
            update_dialog = UpdateDialog(self, error=str(error))
        else:
            update_dialog = UpdateDialog(self, status=update_status)
        finally:
            QApplication.restoreOverrideCursor()

        return update_dialog.exec()

    def _update_window_title(self) -> None:
        filename = os.path.basename(
            self.app_state.current_file_path) if self.app_state.current_file_path else config.UNTITLED_NAME
        dirty_marker = config.DIRTY_MARKER if self.app_state.is_dirty else ""
        return self.setWindowTitle(config.WINDOW_TITLE_FMT.format(marker=dirty_marker, name=filename))

    def _update_status_bar(self, col: int, row: int, color: QColor) -> None:
        try:
            self.status_bar.showMessage(f"x={col}, y={row} | color={color.name(QColor.NameFormat.HexArgb)}")
        except RuntimeError as error:
            get_logger().debug("Skipping status bar update after widget teardown: %s", error)

    def _schedule_preview_refresh(self) -> None:
        if not self._preview_dirty:
            self._preview_dirty = True
            QTimer.singleShot(50, self._refresh_preview)

    def _update_canvas_info(self) -> None:
        self.canvas_info_label.setText(f"{self.canvas.columns} x {self.canvas.rows}px")

    def _update_zoom_label(self, zoom: int) -> None:
        self.zoom_value_label.setText(f"{zoom}x")

    def _on_canvas_zoom_changed(self, zoom: int) -> None:
        if self._fit_zoom_active and not self._applying_fit_zoom:
            self._fit_zoom_active = False
        self._sync_zoom_controls(zoom)

    def _set_zoom_from_slider(self, zoom: int) -> None:
        self.set_zoom(zoom)

    def _apply_zoom_combo_selection(self, index: int) -> None:
        data = self.zoom_preset_combo.itemData(index)
        if data == "fit":
            self.fit_canvas_to_window()
        elif isinstance(data, int):
            self.set_zoom(data)

    def _sync_zoom_controls(self, zoom: int) -> None:
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(zoom)
        self.zoom_slider.blockSignals(False)
        self._sync_zoom_combo(zoom)
        self._update_zoom_label(zoom)

    def _sync_zoom_combo(self, zoom: int) -> None:
        self.zoom_preset_combo.blockSignals(True)
        selected_index = 0
        if self._fit_zoom_active:
            selected_index = self.zoom_preset_combo.findData("fit")
        else:
            preset_index = self.zoom_preset_combo.findData(zoom)
            if preset_index >= 0:
                selected_index = preset_index
        self.zoom_preset_combo.setCurrentIndex(selected_index)
        self.zoom_preset_combo.blockSignals(False)

    def _zoom_percent_label(self, zoom: int) -> str:
        return f"{zoom * 100}%"

    def _on_primary_color_changed(self, color: QColor) -> None:
        self.color_palette.set_primary_color(color)
        self.color_palette.remember_color(color)

    def _on_secondary_color_changed(self, color: QColor) -> None:
        self.color_palette.set_secondary_color(color)
        self.color_palette.remember_color(color)

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

            reply = ask_choice(
                self, config.TITLE_UNSAVED, config.MSG_SAVE_BEFORE_QUIT,
                (
                    (config.BTN_CANCEL, "cancel", "secondary"),
                    (config.BTN_DISCARD, "discard", "danger"),
                    (config.BTN_SAVE, "save", "primary"),
                ),
                "save",
            )
            if reply == "save":
                if self.file_manager.save_file():
                    return event.accept()
                else:
                    return event.ignore()
            elif reply == "cancel" or reply is None:
                return event.ignore()
            else:
                return event.accept()
        else:
            return event.accept()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if (
            watched is self.canvas_scroll_area.viewport()
            and event.type() == QEvent.Type.Resize
            and self._fit_zoom_active
        ):
            QTimer.singleShot(0, self.fit_canvas_to_window)
        return super().eventFilter(watched, event)
