import os, sys
from typing import List, Dict, Any
from PySide6.QtGui import QColor

def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

APP_NAME = "Tilf - Pixel Art Editor"
DEFAULT_WIDTH = 16
DEFAULT_HEIGHT = 16
DEFAULT_ZOOM = 35
HISTORY_LIMIT = 50
AUTOSAVE_DIR = "tilf_autosaves"

DEFAULT_PRIMARY_COLOR = QColor("black")
DEFAULT_SECONDARY_COLOR = QColor("white")
DEFAULT_GRID_COLOR = QColor(80, 80, 80, 160)
CHECKERBOARD_COLOR_1 = QColor(220, 220, 220, 190)
CHECKERBOARD_COLOR_2 = QColor(180, 180, 180, 150)

# The key (e.g., "pencil") is like the tool ID
TOOLS: Dict[str, Dict[str, Any]] = {
    "pencil": {
        "text": "Pencil", "icon": "assets/icons/pencil.png", "shortcut": "B",
        "tooltip": "Draw with the primary color. Hold Alt to use secondary color."
    },
    "eraser": {
        "text": "Eraser", "icon": "assets/icons/eraser.png", "shortcut": "E",
        "tooltip": "Erase pixels to the secondary (background) color."
    },
    "fill": {
        "text": "Bucket", "icon": "assets/icons/bucket.png", "shortcut": "G",
        "tooltip": "Fill an area with the primary color."
    },
    "eyedropper": {
        "text": "Picker", "icon": "assets/icons/picker.png", "shortcut": "I",
        "tooltip": "Pick a color from the canvas. Right-click is a shortcut."
    },
    "rect": {
        "text": "Square", "icon": "assets/icons/square.png", "shortcut": "R",
        "tooltip": "Draw a rectangle. Hold Shift for a perfect square."
    },
    "ellipse": {
        "text": "Circle", "icon": "assets/icons/circle.png", "shortcut": "C",
        "tooltip": "Draw an ellipse. Hold Shift for a perfect circle."
    },
}

# This data structure drives the creation of the toolbar.
# "handler" is the name of the method to be called on the TilfEditor class or its components.
TOOLBAR_ACTIONS: List[Dict[str, Any]] = [
    {"text": "New", "icon": "assets/icons/file.png", "shortcut": "Ctrl+N", "handler_name": "new_file"},
    {"text": "Open", "icon": "assets/icons/open.png", "shortcut": "Ctrl+O", "handler_name": "open_file"},
    {"text": "Save", "icon": "assets/icons/save.png", "shortcut": "Ctrl+S", "handler_name": "save_file"},
    {"sep": True},
    {"text": "Undo", "icon": "assets/icons/arrow_back.png", "shortcut": "Ctrl+Z", "handler_name": "undo"},
    {"text": "Redo", "icon": "assets/icons/arrow_forward.png", "shortcut": "Ctrl+Y", "handler_name": "redo"},
    {"sep": True},
    # The tools will be dynamically inserted here by the Toolbar class
    {"is_tool_group": True},
    {"sep": True},
    {"text": "Color", "icon": "assets/icons/color.png", "handler_name": "choose_primary_color", "tooltip": "Choose primary brush color"},
    {"text": "Background", "icon": "assets/icons/background.png", "handler_name": "choose_secondary_color", "tooltip": "Choose canvas background color"},
    {"text": "Clear", "icon": "assets/icons/clear.png", "handler_name": "clear_canvas", "tooltip": "Clear canvas"},
    {"sep": True},
    {"text": "Grid", "icon": "assets/icons/grid.png", "checkable": True, "checked": True, "handler_name": "toggle_grid"},
    {"text": "Grid color", "icon": "assets/icons/grid_color.png", "handler_name": "choose_grid_color"},
    {"sep": True},
    {"text": "Shift", "icon": "assets/icons/shift.png", "handler_name": "shift_canvas", "tooltip": "Shift canvas up, down, left, or right by 1px."},
    {"sep": True},
    {"text": "About", "icon": "assets/logo.png", "handler_name": "about", "tooltip": "About Tilf"},
]