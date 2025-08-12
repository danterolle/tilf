import sys
import os
import time
from typing import Tuple, Optional, List, Dict, Any

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import (
    QAction, QIcon, QPixmap, QKeySequence, QColor, QDragEnterEvent,
    QImage, QActionGroup
)
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QToolBar, QStatusBar, QColorDialog,
    QFileDialog, QScrollArea, QMessageBox, QLabel, QSlider,
    QHBoxLayout, QDockWidget, QVBoxLayout, QPushButton
)

from pixel_canvas import PixelCanvas
from dialogs import NewImageDialog, AboutDialog, MultipleChoiceDialog
from helper import resource_path


class Tilf(QMainWindow):
    DEFAULT_ZOOM = 35

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Tilf - Pixel Art Editor")
        self.resize(1280, 720)
        self.setAcceptDrops(True)

        self.current_file_path: Optional[str] = None
        self.is_dirty: bool = False

        self.canvas = PixelCanvas()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setWidget(self.canvas)
        self.setCentralWidget(scroll_area)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self._create_zoom_widget()
        self.tool_actions: List[QAction] = []
        self._create_toolbar()
        self._create_preview_dock()
        self._connect_signals()
        self._update_window_title()
        self._set_tool("pencil")
        self._refresh_preview()

    def _create_zoom_widget(self) -> None:
        zoom_widget = QWidget()
        zoom_layout = QHBoxLayout(zoom_widget)
        zoom_layout.setContentsMargins(0, 0, 8, 0)
        zoom_layout.setSpacing(5)

        zoom_slider = QSlider(Qt.Orientation.Horizontal)
        zoom_slider.setMinimum(1)
        zoom_slider.setMaximum(50)
        zoom_slider.setValue(self.DEFAULT_ZOOM)
        zoom_slider.setFixedWidth(150)

        reset_button = QPushButton("Reset Zoom")
        reset_button.setFixedWidth(100)
        reset_button.setToolTip(f"Reset zoom to {self.DEFAULT_ZOOM}x")

        zoom_layout.addWidget(zoom_slider)
        zoom_layout.addWidget(reset_button)

        self.status_bar.addPermanentWidget(zoom_widget)

        zoom_slider.valueChanged.connect(self.canvas.set_cell_size)
        self.canvas.zoom_changed.connect(zoom_slider.setValue)
        reset_button.clicked.connect(lambda: self.canvas.set_cell_size(self.DEFAULT_ZOOM))

    def _create_preview_dock(self) -> None:
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
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Menu")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        style = self.style()

        actions_data: List[Dict[str, Any]] = [
            {
                "custom_icon": resource_path("assets/icons/file.png"),
                "text": "New",
                "shortcut": "Ctrl+N",
                "handler": self._action_new
            },
            {
                "custom_icon": resource_path("assets/icons/open.png"),
                "text": "Open",
                "shortcut": "Ctrl+O",
                "handler": self._action_open
            },
            {
                "custom_icon": resource_path("assets/icons/save.png"),
                "text": "Save",
                "shortcut": "Ctrl+S",
                "handler": self._action_save
            },
            {
                "sep": True
            },
            {
                "custom_icon": resource_path("assets/icons/arrow_back.png"),
                "text": "Undo",
                "shortcut": "Ctrl+Z",
                "handler": self.canvas.undo
            },
            {
                "custom_icon": resource_path("assets/icons/arrow_forward.png"),
                "text": "Redo",
                "shortcut": "Ctrl+Y",
                "handler": self.canvas.redo
            },
            {
                "sep": True
            },
            {
                "custom_icon": resource_path("assets/icons/pencil.png"),
                "text": "Pencil",
                "shortcut": "B",
                "checkable": True,
                "tool": "pencil"
            },
            {
                "custom_icon": resource_path("assets/icons/eraser.png"),
                "text": "Eraser",
                "shortcut": "E",
                "checkable": True,
                "tool": "eraser"
            },
            {
                "custom_icon": resource_path("assets/icons/bucket.png"),
                "text": "Bucket",
                "shortcut": "G",
                "checkable": True,
                "tool": "fill"
            },
            {
                "custom_icon": resource_path("assets/icons/picker.png"),
                "text": "Picker",
                "shortcut": "I",
                "checkable": True,
                "tool": "eyedropper"
            },
            {
                "custom_icon": resource_path("assets/icons/square.png"),
                "text": "Square",
                "shortcut": "R",
                "checkable": True,
                "tool": "rect"
            },
            {
                "custom_icon": resource_path("assets/icons/circle.png"),
                "text": "Circle",
                "shortcut": "C",
                "checkable": True,
                "tool": "ellipse"
            },
            {
                "sep": True
            },
            {
                "custom_icon": resource_path("assets/icons/color.png"),
                "text": "Color",
                "handler": self._choose_color,
                "tooltip": "Choose brush color"
            },
            {
                "custom_icon": resource_path("assets/icons/background.png"),
                "text": "Background",
                "handler": self._choose_background_color,
                "tooltip": "Choose canvas background color"
            },
            {
                "custom_icon": resource_path("assets/icons/clear.png"),
                "text": "Clear",
                "handler": self._action_clear,
                "tooltip": "Clear canvas"
            },
            {
                "sep": True
            },
            {
                "custom_icon": resource_path("assets/icons/grid.png"),
                "text": "Grid",
                "checkable": True,
                "checked": self.canvas.is_grid_visible,
                "handler": self._toggle_grid
            },
            {
                "custom_icon": resource_path("assets/icons/grid_color.png"),
                "text": "Grid color",
                "handler": self._choose_grid_color
            },
            {
                "sep": True
            },
            {
                "custom_icon": resource_path("assets/icons/shift.png"),
                "text": "Shift",
                "shortcut": "S",
                "handler": self._shift_canvas,
                "tooltip": "Shift canvas up, down, left, or right."
            },
            {
                "sep": True
            },
            {
                "custom_icon": resource_path("assets/logo.png"),
                "text": "About Tilf",
                "handler": self._action_about,
                "tooltip": "About Tilf"
            },
        ]

        tools_group = QActionGroup(self)
        tools_group.setExclusive(True)

        for data in actions_data:
            if data.get("sep"): toolbar.addSeparator(); continue

            icon = QIcon()
            if "std_icon" in data:
                icon = style.standardIcon(data["std_icon"])
            elif "custom_icon" in data:
                icon = QIcon(data["custom_icon"])

            action = QAction(icon, data["text"], self)
            if "shortcut" in data: action.setShortcut(QKeySequence(data["shortcut"]))
            if "checkable" in data: action.setCheckable(True)
            if "checked" in data: action.setChecked(True)

            if "tool" in data:
                action.setData(data["tool"])
                action.triggered.connect(lambda checked, tool=data["tool"]: self._set_tool(tool))
                tools_group.addAction(action)
                self.tool_actions.append(action)
            elif "handler" in data:
                action.triggered.connect(data["handler"])

            tooltip_text = data.get("tooltip", data['text'])
            shortcut_text = f" ({data['shortcut']})" if 'shortcut' in data else ""
            action.setToolTip(f"{tooltip_text}{shortcut_text}")
            toolbar.addAction(action)

    def _connect_signals(self) -> None:
        self.canvas.pixel_hovered.connect(self._update_status)
        self.canvas.zoom_changed.connect(lambda v: self._safe_show_status(f"Zoom: {v}x", 1500))
        self.canvas.image_changed.connect(self._on_image_changed)
        self.canvas.color_picked.connect(self._on_color_picked)
        self.canvas.tool_change_requested.connect(self._set_tool)

    def _set_tool(self, tool: str) -> None:
        self.canvas.set_tool(tool)
        self._safe_show_status(f"Tool: {tool.capitalize()}", 1200)
        for action in self.tool_actions:
            if action.data() == tool:
                action.setChecked(True)
                break

    def _on_color_picked(self, color: QColor) -> None:
        if color.isValid():
            self.canvas.current_color = color
            self._safe_show_status(f"Color selected: {color.name()}", 2000)

    def _action_new(self) -> None:
        if not self._confirm_discard_if_needed(): return
        dialog = NewImageDialog(self)
        if dialog.exec():
            width, height = dialog.get_size()
            self.canvas.reset_canvas(width, height, clear_history=True)
            self.current_file_path, self.is_dirty = None, False
            self._update_window_title()

    def _action_open(self, path: Optional[str] = None) -> None:
        if not self._confirm_discard_if_needed(): return
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            img = QImage(path)
            if img.isNull():
                QMessageBox.warning(self, "Error", "Failed to load the image.")
            else:
                self.canvas.load_image(img)
                self.current_file_path, self.is_dirty = path, False
                self._update_window_title()

    def _action_save(self) -> None:
        path, file_format, is_transparent = self._prompt_save_path_and_options()
        if not path: return
        self.canvas.export_image(path, file_format, is_transparent)
        self.current_file_path, self.is_dirty = path, False
        self._update_window_title()
        self._safe_show_status(f"Saved: {os.path.basename(path)}", 3000)

    def _action_clear(self) -> None:
        reply = QMessageBox.question(
            self, "Clear Canvas", "Are you sure you want to clear the canvas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.canvas.clear_canvas()

    def _action_about(self) -> None:
        AboutDialog(self).exec()

    def _choose_color(self) -> None:
        color = QColorDialog.getColor(self.canvas.current_color, self, "Choose Brush Color")
        if color.isValid(): self.canvas.current_color = color

    def _choose_background_color(self) -> None:
        color = QColorDialog.getColor(
            self.canvas.base_color,
            self,
            "Choose Background Color",
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )
        if color.isValid():
            self.canvas.set_background_color(color)

    def _choose_grid_color(self) -> None:
        color = QColorDialog.getColor(self.canvas.grid_color, self, "Choose Grid Color")
        if color.isValid():
            self.canvas.grid_color = color
            self.canvas.update()

    def _shift_canvas(self) -> None:
        shift_options = ["Left", "Right", "Top", "Bottom"]
        shift_selection_dialog = MultipleChoiceDialog("Shift Canvas", "Shift canvas 1px to the:", shift_options, self)
        if shift_selection_dialog.exec():
            selected_option = shift_selection_dialog.get_selected_option()
            if not selected_option:
                pass
            else:
                self.canvas.shift_image(selected_option.lower())

    def _toggle_grid(self, checked: bool) -> None:
        self.canvas.is_grid_visible = checked
        self.canvas.update()

    def _on_image_changed(self) -> None:
        self.is_dirty = True
        self._update_window_title()
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        if self.canvas.image.isNull(): return

        preview_widget_size = self.preview_label.size()
        if not preview_widget_size.isValid():
            preview_widget_size = QSize(150, 150)

        pixmap = QPixmap.fromImage(self.canvas.image)
        scaled_pixmap = pixmap.scaled(
            preview_widget_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)

    def _update_status(self, col: int, row: int, color: QColor) -> None:
        try:
            self.status_bar.showMessage(f"x={col}, y={row} | color={color.name(QColor.NameFormat.HexArgb)}")
        except RuntimeError:
            pass

    def _safe_show_status(self, text: str, timeout: int = 0) -> None:
        try:
            if hasattr(self, 'status_bar') and self.status_bar:
                self.status_bar.showMessage(text, timeout)
        except RuntimeError:
            pass

    def _update_window_title(self) -> None:
        filename = os.path.basename(self.current_file_path) if self.current_file_path else "Untitled"
        dirty_marker = "*" if self.is_dirty else ""
        self.setWindowTitle(f"{dirty_marker}{filename} - Tilf")

    def _confirm_discard_if_needed(self) -> bool:
        if not self.is_dirty: return True
        reply = QMessageBox.question(
            self, "Unsaved Changes", "Continue and discard changes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def _prompt_save_path_and_options(self) -> Tuple[Optional[str], Optional[str], bool]:
        path, selected_filter = QFileDialog.getSaveFileName(
            self, "Save Image", self.current_file_path or "sprite.png",
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)"
        )

        if not path:
            return None, None, False

        file_ext = os.path.splitext(path)[1].upper().replace('.', '')

        if file_ext in ("JPG", "JPEG"):
            file_format = "JPEG"
        elif file_ext == "PNG":
            file_format = "PNG"
        elif file_ext == "BMP":
            file_format = "BMP"
        else:
            if "JPEG" in selected_filter:
                file_format = "JPEG"
            elif "BMP" in selected_filter:
                file_format = "BMP"
            else: file_format = "PNG"

        is_transparent = False
        if file_format == "PNG":
            reply = QMessageBox.question(
                self, "Transparency", "Keep transparent background?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            is_transparent = (reply == QMessageBox.StandardButton.Yes)

        return path, file_format, is_transparent

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        mime_data = event.mimeData()
        if mime_data.hasUrls() and any(
                u.isLocalFile() and u.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')) for u in
                mime_data.urls()):
            event.acceptProposedAction()

    def dropEvent(self, event: QDragEnterEvent) -> None:
        if not self._confirm_discard_if_needed():
            event.ignore()
            return
        url = next((u for u in event.mimeData().urls() if u.isLocalFile()), None)
        if url:
            self._action_open(path=url.toLocalFile())
            event.acceptProposedAction()

    def closeEvent(self, event) -> None:
        if self.is_dirty:
            try:
                script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                autosaves_dir = os.path.join(script_dir, "tilf_autosaves")
                os.makedirs(autosaves_dir, exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                basename = os.path.splitext(os.path.basename(self.current_file_path or "sprite"))[0]
                autosave_path = os.path.join(autosaves_dir, f"{basename}_{timestamp}.png")
                self.canvas.export_image(autosave_path, "PNG", is_transparent=True)
                print(f"Autosaved recovery file to: {autosave_path}")
            except Exception as e:
                print(f"Error during autosave: {e}", file=sys.stderr)
        super().closeEvent(event)