from dataclasses import dataclass


class ToolType:
    PENCIL = "pencil"
    ERASER = "eraser"
    FILL = "fill"
    EYEDROPPER = "eyedropper"
    RECT = "rect"
    ELLIPSE = "ellipse"


@dataclass(frozen=True)
class ToolDefinition:
    text: str
    icon: str
    shortcut: str
    tooltip: str


@dataclass(frozen=True)
class ToolbarAction:
    text: str = ""
    icon: str = ""
    shortcut: str | None = None
    handler_name: str | None = None
    tooltip: str | None = None
    checkable: bool = False
    checked: bool = False
    separator: bool = False
    tool_group: bool = False


TOOLS: dict[str, ToolDefinition] = {
    ToolType.PENCIL: ToolDefinition(
        text="Pencil",
        icon="assets/icons/pencil.png",
        shortcut="B",
        tooltip="Draw with the primary color. Hold Alt to use secondary color.",
    ),
    ToolType.ERASER: ToolDefinition(
        text="Eraser",
        icon="assets/icons/eraser.png",
        shortcut="E",
        tooltip="Erase pixels to the secondary (background) color.",
    ),
    ToolType.FILL: ToolDefinition(
        text="Fill",
        icon="assets/icons/bucket.png",
        shortcut="G",
        tooltip="Fill an area with the primary color.",
    ),
    ToolType.EYEDROPPER: ToolDefinition(
        text="Eyedropper",
        icon="assets/icons/picker.png",
        shortcut="I",
        tooltip="Pick a color from the canvas. Right-click is a shortcut.",
    ),
    ToolType.RECT: ToolDefinition(
        text="Rectangle",
        icon="assets/icons/square.png",
        shortcut="R",
        tooltip="Draw a rectangle. Hold Shift for a perfect square.",
    ),
    ToolType.ELLIPSE: ToolDefinition(
        text="Ellipse",
        icon="assets/icons/circle.png",
        shortcut="C",
        tooltip="Draw an ellipse. Hold Shift for a perfect circle.",
    ),
}

TOOLBAR_ACTIONS: tuple[ToolbarAction, ...] = (
    ToolbarAction(text="New", icon="assets/icons/file.png", shortcut="Ctrl+N", handler_name="new_file"),
    ToolbarAction(text="Open", icon="assets/icons/open.png", shortcut="Ctrl+O", handler_name="open_file"),
    ToolbarAction(text="Save", icon="assets/icons/save.png", shortcut="Ctrl+S", handler_name="save_file"),
    ToolbarAction(separator=True),
    ToolbarAction(text="Undo", icon="assets/icons/arrow_back.png", shortcut="Ctrl+Z", handler_name="undo"),
    ToolbarAction(text="Redo", icon="assets/icons/arrow_forward.png", shortcut="Ctrl+Y", handler_name="redo"),
    ToolbarAction(separator=True),
    ToolbarAction(tool_group=True),
    ToolbarAction(separator=True),
    ToolbarAction(
        text="Color",
        icon="assets/icons/color.png",
        handler_name="choose_primary_color",
        tooltip="Choose primary brush color",
    ),
    ToolbarAction(
        text="Background",
        icon="assets/icons/background.png",
        handler_name="choose_secondary_color",
        tooltip="Choose canvas background color",
    ),
    ToolbarAction(separator=True),
    ToolbarAction(text="Clear", icon="assets/icons/clear.png", handler_name="clear_canvas", tooltip="Clear canvas"),
    ToolbarAction(
        text="Shift",
        icon="assets/icons/shift.png",
        handler_name="shift_canvas",
        tooltip="Shift canvas up, down, left, or right by 1px.",
    ),
    ToolbarAction(separator=True),
    ToolbarAction(
        text="Grid",
        icon="assets/icons/grid.png",
        handler_name="toggle_grid",
        checkable=True,
        checked=True,
    ),
    ToolbarAction(text="Grid color", icon="assets/icons/grid_color.png", handler_name="choose_grid_color"),
    ToolbarAction(separator=True),
    ToolbarAction(
        text="Update",
        icon="assets/icons/update.png",
        handler_name="check_for_updates",
        tooltip="Check for updates",
    ),
    ToolbarAction(text="About", icon="assets/logo.png", handler_name="about", tooltip="About Tilf"),
)
