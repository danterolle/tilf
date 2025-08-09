import sys
from PySide6.QtWidgets import QApplication

from editor import Tilf

def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    try:
        with open("style.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("style.qss not found.")

    window = Tilf()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()