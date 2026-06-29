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
            width, height, tile_cols, tile_rows, tile_size = dialog.get_size()
            self.canvas.reset_canvas(
                width, height, clear_history=True,
                tile_cols=tile_cols, tile_rows=tile_rows, tile_size=tile_size,
            )
            self.app_state.set_file_path(None)

    def open_file(self, path: Optional[str] = None):
        if not self._confirm_discard_if_needed():
            return
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self.parent,
                config.TITLE_OPEN_IMAGE,
                "",
                config.OPEN_FILE_FILTER
            )

        if path:
            image = QImage(path)
            if image.isNull():
                QMessageBox.warning(self.parent, config.TITLE_ERROR, config.MSG_FAILED_LOAD)
            else:
                self.canvas.load_image(image)
                self.app_state.set_file_path(path)

    def save_file(self) -> bool:
        path = self.app_state.current_file_path
        if not path:
            return self.save_file_as()

        file_ext = os.path.splitext(path)[1].upper().replace('.', '')
        file_format = (
            config.IMAGE_FORMAT_JPEG if file_ext in config.JPEG_EXTENSIONS
            else config.IMAGE_FORMAT_BMP if file_ext == config.IMAGE_FORMAT_BMP
            else config.IMAGE_FORMAT_PNG
        )

        is_transparent = (file_format == config.IMAGE_FORMAT_PNG)

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
            timestamp = time.strftime(config.AUTOSAVE_TIMESTAMP_FORMAT)
            basename = os.path.splitext(os.path.basename(self.app_state.current_file_path or ""))[0] or "sprite"
            autosave_path = os.path.join(autosaves_dir, f"{basename}_{timestamp}.png")
            self.export_image(autosave_path, config.IMAGE_FORMAT_PNG, is_transparent=True)
            print(config.MSG_AUTOSAVE_SUCCESS_FMT.format(path=autosave_path))
        except Exception as e:
            print(config.MSG_AUTOSAVE_ERROR_FMT.format(error=e), file=sys.stderr)


    def export_image(self, filename: str, file_format: Optional[str], is_transparent: bool) -> None:
        img_to_save = self.canvas.image.copy()
        if not is_transparent:
            background_img = QImage(img_to_save.size(), QImage.Format.Format_ARGB32)
            background_img.fill(QColor(config.COLOR_WHITE))
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
            config.TITLE_UNSAVED,
            config.MSG_DISCARD_CHANGES,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def _prompt_save_path_and_options(self) -> Tuple[Optional[str], Optional[str], bool]:
        path, selected_filter = QFileDialog.getSaveFileName(
            self.parent, config.TITLE_SAVE_IMAGE, self.app_state.current_file_path or config.DEFAULT_FILENAME,
            config.SAVE_FILE_FILTER
        )
        if not path:
            return None, None, False

        file_ext = os.path.splitext(path)[1].upper().replace('.', '')
        if file_ext in config.JPEG_EXTENSIONS:
            file_format = config.IMAGE_FORMAT_JPEG
        elif file_ext == config.IMAGE_FORMAT_BMP:
            file_format = config.IMAGE_FORMAT_BMP
        else:
            file_format = config.IMAGE_FORMAT_PNG

        is_transparent = False
        if file_format == config.IMAGE_FORMAT_PNG:
            reply = QMessageBox.question(
                self.parent,
                config.TITLE_TRANSPARENCY,
                config.MSG_TRANSPARENCY_PROMPT,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            is_transparent = (reply == QMessageBox.StandardButton.Yes)

        return path, file_format, is_transparent