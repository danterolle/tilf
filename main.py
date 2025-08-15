import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from state import AppState
from ui.editor import TilfEditor
from config import resource_path

def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Tilf - Pixel Art Editor")
    app.setQuitOnLastWindowClosed(True)

    app_icon_path = resource_path("assets/icon.icns")
    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))
    else:
        print(f"Tilf icon not found at: {app_icon_path}")

    stylesheet_path = resource_path("style.qss")
    try:
        with open(stylesheet_path, "r") as f:
            app.setStyleSheet(f.read())
        print(f"Stylesheet loaded from: {stylesheet_path}")
    except FileNotFoundError:
        print(f"Stylesheet not found at: {stylesheet_path}. Running with default style.")

    app_state = AppState()

    window = TilfEditor(app_state)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()