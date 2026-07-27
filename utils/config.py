from typing import Any, Dict, List

from PySide6.QtGui import QColor

APP_NAME = "Tilf - Pixel Art Editor"
DEFAULT_TILE_COLS = 8
DEFAULT_TILE_ROWS = 6
DEFAULT_TILE_SIZE = 16
DEFAULT_WIDTH = DEFAULT_TILE_COLS * DEFAULT_TILE_SIZE
DEFAULT_HEIGHT = DEFAULT_TILE_ROWS * DEFAULT_TILE_SIZE
DEFAULT_ZOOM = 35
HISTORY_LIMIT = 50
AUTOSAVE_DIR = "tilf_autosaves"

MAX_TILE_COLS = 64
MAX_TILE_ROWS = 64
MIN_TILE_SIZE = 8
MAX_TILE_SIZE = 128

DEFAULT_PRIMARY_COLOR = QColor("black")
DEFAULT_SECONDARY_COLOR = QColor("white")
DEFAULT_GRID_COLOR = QColor(80, 80, 80, 160)
CHECKERBOARD_COLOR_1 = QColor(220, 220, 220, 190)
CHECKERBOARD_COLOR_2 = QColor(180, 180, 180, 150)

# --- File I/O ---
OPEN_FILE_FILTER = "Images (*.png *.jpg *.jpeg *.bmp)"
SAVE_FILE_FILTER = "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)"
SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp")
JPEG_EXTENSIONS = ("JPG", "JPEG")
IMAGE_FORMAT_PNG = "PNG"
IMAGE_FORMAT_JPEG = "JPEG"
IMAGE_FORMAT_BMP = "BMP"
DEFAULT_FILENAME = "sprite.png"
COLOR_WHITE = "white"
COLOR_TRANSPARENT = "transparent"
AUTOSAVE_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# --- UI ---
TITLE_ERROR = "Error"
TITLE_UNSAVED = "Unsaved Changes"
TITLE_TRANSPARENCY = "Transparency"
TITLE_CLEAR_CANVAS = "Clear Canvas"
TITLE_SHIFT_CANVAS = "Shift Canvas"
TITLE_NEW_CANVAS = "New Canvas"
TITLE_ABOUT = "About Tilf"
TITLE_OPEN_IMAGE = "Open Image"
TITLE_SAVE_IMAGE = "Save Image"
TITLE_PRIMARY_COLOR = "Choose Primary Color"
TITLE_SECONDARY_COLOR = "Choose Secondary Color"
TITLE_GRID_COLOR = "Choose Grid Color"

MSG_FAILED_LOAD = "Failed to load the image."
MSG_FAILED_SAVE_FMT = "Failed to save the image to: {path}"
MSG_DISCARD_CHANGES = "You have unsaved changes. Do you want to continue and discard them?"
MSG_SAVE_BEFORE_QUIT = "You have unsaved changes. Do you want to save before quitting?"
MSG_TRANSPARENCY_PROMPT = "Save with a transparent background?"
MSG_CLEAR_CONFIRM = "Are you sure you want to clear the canvas?"
MSG_SHIFT_CANVAS = "Shift canvas 1px to the:"

LABEL_WIDTH = "Width (px):"
LABEL_HEIGHT = "Height (px):"
BTN_OK = "OK"
BTN_CANCEL = "Cancel"
BTN_RESET_ZOOM = "Reset Zoom"
LABEL_PREVIEW = "Preview"
TOOLBAR_TITLE = "Main Toolbar"

DIRTY_MARKER = "*"
UNTITLED_NAME = "Untitled"
WINDOW_TITLE_FMT = "{marker}{name} - " + APP_NAME
RESET_ZOOM_TOOLTIP_FMT = "Reset zoom to {zoom}x"

# --- Canvas shift directions ---
SHIFT_OPTIONS = ["Left", "Right", "Up", "Down"]
SHIFT_OFFSETS = {
    "right": (1, 0),
    "left": (-1, 0),
    "down": (0, 1),
    "up": (0, -1),
}

# --- Assets ---
ICON_FILENAME = "icon.icns"
STYLESHEET_FILENAME = "style.qss"
LOGO_RESOURCE = "assets/logo.png"

# --- Console messages ---
MSG_ICON_NOT_FOUND_FMT = "Tilf icon not found at: {path}"
MSG_STYLESHEET_LOADED_FMT = "Stylesheet loaded from: {path}"
MSG_STYLESHEET_MISSING_FMT = "Stylesheet not found at: {path}. Running with default style."
MSG_AUTOSAVE_SUCCESS_FMT = "Autosaved recovery file to: {path}"
MSG_AUTOSAVE_ERROR_FMT = "Error during autosave: {error}"
MSG_TOOL_WARNING_FMT = "Warning: Tool '{tool_name}' not found."

class ToolType:
    PENCIL = "pencil"
    ERASER = "eraser"
    FILL = "fill"
    EYEDROPPER = "eyedropper"
    RECT = "rect"
    ELLIPSE = "ellipse"

# The key (e.g., "pencil") is like the tool ID
TOOLS: Dict[str, Dict[str, Any]] = {
    ToolType.PENCIL: {
        "text": "Pencil", "icon": "assets/icons/pencil.png", "shortcut": "B",
        "tooltip": "Draw with the primary color. Hold Alt to use secondary color."
    },
    ToolType.ERASER: {
        "text": "Eraser", "icon": "assets/icons/eraser.png", "shortcut": "E",
        "tooltip": "Erase pixels to the secondary (background) color."
    },
    ToolType.FILL: {
        "text": "Fill", "icon": "assets/icons/bucket.png", "shortcut": "G",
        "tooltip": "Fill an area with the primary color."
    },
    ToolType.EYEDROPPER: {
        "text": "Eyedropper", "icon": "assets/icons/picker.png", "shortcut": "I",
        "tooltip": "Pick a color from the canvas. Right-click is a shortcut."
    },
    ToolType.RECT: {
        "text": "Rectangle", "icon": "assets/icons/square.png", "shortcut": "R",
        "tooltip": "Draw a rectangle. Hold Shift for a perfect square."
    },
    ToolType.ELLIPSE: {
        "text": "Ellipse", "icon": "assets/icons/circle.png", "shortcut": "C",
        "tooltip": "Draw an ellipse. Hold Shift for a perfect circle."
    },
}

# This data structure drives the creation of the toolbar.
# "handler" is the name of the method to be called on the TilfEditor class or its components.
TOOLBAR_ACTIONS: List[Dict[str, Any]] = [
    {"section": "File"},
    {"text": "New", "icon": "assets/icons/file.png", "shortcut": "Ctrl+N", "handler_name": "new_file"},
    {"text": "Open", "icon": "assets/icons/open.png", "shortcut": "Ctrl+O", "handler_name": "open_file"},
    {"text": "Save", "icon": "assets/icons/save.png", "shortcut": "Ctrl+S", "handler_name": "save_file"},
    {"sep": True},
    {"section": "Edit"},
    {"text": "Undo", "icon": "assets/icons/arrow_back.png", "shortcut": "Ctrl+Z", "handler_name": "undo"},
    {"text": "Redo", "icon": "assets/icons/arrow_forward.png", "shortcut": "Ctrl+Y", "handler_name": "redo"},
    {"sep": True},
    {"section": "Tools"},
    {"is_tool_group": True},
    {"sep": True},
    {"section": "Colors"},
    {
        "text": "Color", "icon": "assets/icons/color.png",
        "handler_name": "choose_primary_color", "tooltip": "Choose primary brush color",
    },
    {
        "text": "Background", "icon": "assets/icons/background.png",
        "handler_name": "choose_secondary_color", "tooltip": "Choose canvas background color",
    },
    {"sep": True},
    {"section": "Canvas"},
    {"text": "Clear", "icon": "assets/icons/clear.png", "handler_name": "clear_canvas", "tooltip": "Clear canvas"},
    {
        "text": "Shift", "icon": "assets/icons/shift.png",
        "handler_name": "shift_canvas", "tooltip": "Shift canvas up, down, left, or right by 1px.",
    },
    {"sep": True},
    {"section": "View"},
    {
        "text": "Grid", "icon": "assets/icons/grid.png",
        "checkable": True, "checked": True, "handler_name": "toggle_grid",
    },
    {"text": "Grid color", "icon": "assets/icons/grid_color.png", "handler_name": "choose_grid_color"},
    {"sep": True},
    {"section": "Help"},
    {"text": "About", "icon": "assets/logo.png", "handler_name": "about", "tooltip": "About Tilf"},
]
