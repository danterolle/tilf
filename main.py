import sys
import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from editor import Tilf
from helper import resource_path

def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Tilf - Pixel Art Editor")
    app.setQuitOnLastWindowClosed(True)

    app_icon_path = resource_path("resources/icon.icns")
    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))

    stylesheet_path = resource_path("style.qss")
    try:
        with open(stylesheet_path, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"Stylesheet not found at: {stylesheet_path}")

    window = Tilf()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()