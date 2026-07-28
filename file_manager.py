import os
import sys
import time

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from state import AppState
from ui.canvas import Canvas
from ui.dialogs.new_canvas import NewCanvas
from utils import config
from utils.image_io import export_image as save_image
from utils.image_io import infer_image_format
from utils.log import get_logger


class FileManager:
    def __init__(self, parent_widget: QWidget, app_state: AppState, canvas: Canvas) -> None:
        self.parent = parent_widget
        self.app_state = app_state
        self.canvas = canvas

    def new_file(self) -> None:
        if not self._confirm_discard_if_needed():
            return
        dialog = NewCanvas(self.parent)
        if dialog.exec():
            width, height, tile_size = dialog.get_size()
            self.canvas.reset_canvas(
                width, height, clear_history=True,
                tile_size=tile_size,
            )
            self.app_state.set_file_path(None)

    def open_file(self, path: str | None = None) -> None:
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

        file_format = infer_image_format(path)
        is_transparent = (file_format == config.IMAGE_FORMAT_PNG)

        if not save_image(self.canvas.image, path, file_format, is_transparent):
            self._show_save_error(path)
            return False

        self.app_state.set_dirty(False)
        return True

    def save_file_as(self) -> bool:
        path, file_format, is_transparent = self._prompt_save_path_and_options()
        if not path:
            return False

        if not save_image(self.canvas.image, path, file_format, is_transparent):
            self._show_save_error(path)
            return False

        self.app_state.set_file_path(path)
        self.app_state.set_dirty(False)
        return True

    def autosave_on_exit(self) -> None:
        if not self.app_state.is_dirty:
            return

        try:
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            autosaves_dir = os.path.join(script_dir, config.AUTOSAVE_DIR)
            os.makedirs(autosaves_dir, exist_ok=True)
            timestamp = time.strftime(config.AUTOSAVE_TIMESTAMP_FORMAT)
            basename = os.path.splitext(os.path.basename(self.app_state.current_file_path or ""))[0] or "sprite"
            autosave_path = os.path.join(autosaves_dir, f"{basename}_{timestamp}.png")

            if save_image(self.canvas.image, autosave_path, config.IMAGE_FORMAT_PNG, is_transparent=True):
                get_logger().info(config.MSG_AUTOSAVE_SUCCESS_FMT.format(path=autosave_path))
            else:
                get_logger().error(
                    config.MSG_AUTOSAVE_ERROR_FMT.format(error=f"failed to save {autosave_path}")
                )
        except OSError as error:
            get_logger().error(config.MSG_AUTOSAVE_ERROR_FMT.format(error=error))

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

    def _prompt_save_path_and_options(self) -> tuple[str | None, str | None, bool]:
        path, _ = QFileDialog.getSaveFileName(
            self.parent,
            config.TITLE_SAVE_IMAGE,
            self.app_state.current_file_path or config.DEFAULT_FILENAME,
            config.SAVE_FILE_FILTER
        )
        if not path:
            return None, None, False

        file_format = infer_image_format(path)
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

    def _show_save_error(self, path: str) -> None:
        QMessageBox.warning(
            self.parent,
            config.TITLE_ERROR,
            config.MSG_FAILED_SAVE_FMT.format(path=path),
        )
