import sys
from PySide6.QtWidgets import QApplication

from editor import Tilf

def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    app.setStyleSheet("""
        QMainWindow, QDialog { background-color: #2b2b2b; }
        QToolBar { background-color: #3c3f41; spacing: 4px; padding: 6px; border-bottom: 1px solid #444; }
        QToolButton { background: transparent; border: none; padding: 6px; color: #ddd; border-radius: 6px; }
        QToolButton:hover { background-color: rgba(255,255,255,0.06); }
        QToolButton:checked { background-color: rgba(100,150,255,0.18); }
        QToolBar::separator { background-color: #555; width: 1px; margin: 4px 6px; }
        QStatusBar { background-color: #3c3f41; color: #ddd; border-top: 1px solid #444; }
        QLabel { color: #ddd; }
        QDockWidget { background-color: #2b2b2b; }
        QSpinBox, QPushButton { color: #ddd; background-color: #3c3f41; border: 1px solid #555; padding: 4px; border-radius: 3px; }
        QPushButton:hover { background-color: #4c4f51; }
        QSlider::groove:horizontal { height: 6px; background: #555; border-radius: 3px; }
        QSlider::handle:horizontal { width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; background: #ddd; }
    """)

    window = Tilf()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()