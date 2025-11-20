import os
import time
import sys
from typing import Tuple, Optional
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PySide6.QtGui import QImage, QPainter, QColor

from ui.canvas import Canvas
from state import AppState
from utils import config
from ui.dialogs.new_canvas import NewCanvas

class FileManager:
    def __init__(self, parent_widget: QWidget, app_state: AppState, canvas: Canvas):
        self.parent = parent_widget
        self.app_state = app_state
        self.canvas = canvas

    def new_file(self):
        if not self._confirm_discard_if_needed():
            return
        dialog = NewCanvas(self.parent)
        if dialog.exec():
            width, height = dialog.get_size()
            self.canvas.reset_canvas(width, height, clear_history=True)
            self.app_state.set_file_path(None)

    def open_file(self, path: Optional[str] = None):
        if not self._confirm_discard_if_needed():
            return
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self.parent,
                "Open Image",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp)"
            )

        if path:
            image = QImage(path)
            if image.isNull():
                QMessageBox.warning(self.parent, "Error", "Failed to load the image.")
            else:
                self.canvas.load_image(image)
                self.app_state.set_file_path(path)

    def save_file(self) -> bool:
        path = self.app_state.current_file_path
        if not path:
            return self.save_file_as()

        file_ext = os.path.splitext(path)[1].upper().replace('.', '')
        file_format = "JPEG" if file_ext in ("JPG", "JPEG") else "BMP" if file_ext == "BMP" else "PNG"

        is_transparent = (file_format == "PNG")

        self.export_image(path, file_format, is_transparent)
        self.app_state.set_dirty(False)
        return True

    def save_file_as(self) -> bool:
        path, file_format, is_transparent = self._prompt_save_path_and_options()
        if not path:
            return False

        self.export_image(path, file_format, is_transparent)
        self.app_state.set_file_path(path)
        self.app_state.set_dirty(False)
        return True

    def autosave_on_exit(self):
        """ Creates a recovery file if there are unsaved changes on exit. """
        if not self.app_state.is_dirty:
            return
        try:
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            autosaves_dir = os.path.join(script_dir, config.AUTOSAVE_DIR)
            os.makedirs(autosaves_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            basename = os.path.splitext(os.path.basename(self.app_state.current_file_path or "sprite"))[0]
            autosave_path = os.path.join(autosaves_dir, f"{basename}_{timestamp}.png")
            self.export_image(autosave_path, "PNG", is_transparent=True)
            print(f"Autosaved recovery file to: {autosave_path}")
        except Exception as e:
            print(f"Error during autosave: {e}", file=sys.stderr)


    def export_image(self, filename: str, file_format: Optional[str], is_transparent: bool) -> None:
        img_to_save = self.canvas.image.copy()
        if not is_transparent:
            background_img = QImage(img_to_save.size(), QImage.Format.Format_ARGB32)
            background_img.fill(QColor("white"))
            painter = QPainter(background_img)
            painter.drawImage(0, 0, img_to_save)
            painter.end()
            background_img.save(filename, file_format)
        else:
            img_to_save.save(filename, file_format)

    def _confirm_discard_if_needed(self) -> bool:
        if not self.app_state.is_dirty:
            return True
        reply = QMessageBox.question(
            self.parent,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to continue and discard them?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def _prompt_save_path_and_options(self) -> Tuple[Optional[str], Optional[str], bool]:
        path, selected_filter = QFileDialog.getSaveFileName(
            self.parent, "Save Image", self.app_state.current_file_path or "sprite.png",
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)"
        )
        if not path:
            return None, None, False

        file_ext = os.path.splitext(path)[1].upper().replace('.', '')
        if file_ext in ("JPG", "JPEG"):
            file_format = "JPEG"
        elif file_ext == "BMP":
            file_format = "BMP"
        else: file_format = "PNG"

        is_transparent = False
        if file_format == "PNG":
            reply = QMessageBox.question(
                self.parent,
                "Transparency",
                "Save with a transparent background?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            is_transparent = (reply == QMessageBox.StandardButton.Yes)

        return path, file_format, is_transparent