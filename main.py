import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from state import AppState
from ui.editor import TilfEditor
from utils import config
from utils.log import get_logger
from utils.log import setup as setup_logging
from utils.resource_path import get_resource_path


def main() -> None:
    setup_logging()
    logger = get_logger()

    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setQuitOnLastWindowClosed(True)

    app_icon_path = get_resource_path(config.ICON_FILENAME)
    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))
    else:
        logger.warning(config.MSG_ICON_NOT_FOUND_FMT.format(path=app_icon_path))

    stylesheet_path = get_resource_path(config.STYLESHEET_FILENAME)
    try:
        with open(stylesheet_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        logger.info(config.MSG_STYLESHEET_LOADED_FMT.format(path=stylesheet_path))
    except FileNotFoundError:
        logger.warning(config.MSG_STYLESHEET_MISSING_FMT.format(path=stylesheet_path))

    app_state = AppState()

    window = TilfEditor(app_state)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
