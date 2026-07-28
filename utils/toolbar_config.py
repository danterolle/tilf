from typing import Any


class ToolType:
    PENCIL = "pencil"
    ERASER = "eraser"
    FILL = "fill"
    EYEDROPPER = "eyedropper"
    RECT = "rect"
    ELLIPSE = "ellipse"


TOOLS: dict[str, dict[str, Any]] = {
    ToolType.PENCIL: {
        "text": "Pencil", "icon": "assets/icons/pencil.png", "shortcut": "B",
        "tooltip": "Draw with the primary color. Hold Alt to use secondary color.",
    },
    ToolType.ERASER: {
        "text": "Eraser", "icon": "assets/icons/eraser.png", "shortcut": "E",
        "tooltip": "Erase pixels to the secondary (background) color.",
    },
    ToolType.FILL: {
        "text": "Fill", "icon": "assets/icons/bucket.png", "shortcut": "G",
        "tooltip": "Fill an area with the primary color.",
    },
    ToolType.EYEDROPPER: {
        "text": "Eyedropper", "icon": "assets/icons/picker.png", "shortcut": "I",
        "tooltip": "Pick a color from the canvas. Right-click is a shortcut.",
    },
    ToolType.RECT: {
        "text": "Rectangle", "icon": "assets/icons/square.png", "shortcut": "R",
        "tooltip": "Draw a rectangle. Hold Shift for a perfect square.",
    },
    ToolType.ELLIPSE: {
        "text": "Ellipse", "icon": "assets/icons/circle.png", "shortcut": "C",
        "tooltip": "Draw an ellipse. Hold Shift for a perfect circle.",
    },
}

TOOLBAR_ACTIONS: list[dict[str, Any]] = [
    {"text": "New", "icon": "assets/icons/file.png", "shortcut": "Ctrl+N", "handler_name": "new_file"},
    {"text": "Open", "icon": "assets/icons/open.png", "shortcut": "Ctrl+O", "handler_name": "open_file"},
    {"text": "Save", "icon": "assets/icons/save.png", "shortcut": "Ctrl+S", "handler_name": "save_file"},
    {"sep": True},
    {"text": "Undo", "icon": "assets/icons/arrow_back.png", "shortcut": "Ctrl+Z", "handler_name": "undo"},
    {"text": "Redo", "icon": "assets/icons/arrow_forward.png", "shortcut": "Ctrl+Y", "handler_name": "redo"},
    {"sep": True},
    {"is_tool_group": True},
    {"sep": True},
    {
        "text": "Color", "icon": "assets/icons/color.png",
        "handler_name": "choose_primary_color", "tooltip": "Choose primary brush color",
    },
    {
        "text": "Background", "icon": "assets/icons/background.png",
        "handler_name": "choose_secondary_color", "tooltip": "Choose canvas background color",
    },
    {"sep": True},
    {"text": "Clear", "icon": "assets/icons/clear.png", "handler_name": "clear_canvas", "tooltip": "Clear canvas"},
    {
        "text": "Shift", "icon": "assets/icons/shift.png",
        "handler_name": "shift_canvas", "tooltip": "Shift canvas up, down, left, or right by 1px.",
    },
    {"sep": True},
    {
        "text": "Grid", "icon": "assets/icons/grid.png",
        "checkable": True, "checked": True, "handler_name": "toggle_grid",
    },
    {"text": "Grid color", "icon": "assets/icons/grid_color.png", "handler_name": "choose_grid_color"},
    {"sep": True},
    {"text": "About", "icon": "assets/logo.png", "handler_name": "about", "tooltip": "About Tilf"},
]
