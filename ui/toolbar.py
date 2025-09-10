from typing import Dict, Any
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence, QActionGroup
from PySide6.QtWidgets import QToolBar, QMainWindow
from state import AppState
from utils import config, resource_path


class Toolbar:
    def __init__(self, main_window: QMainWindow, app_state: AppState, handlers: Dict[str, callable]):
        self.main_window = main_window
        self.app_state = app_state
        self.handlers = handlers
        self.tool_actions: Dict[str, QAction] = {}

    def create_toolbar(self) -> QToolBar:
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setMovable(False)

        for data in config.TOOLBAR_ACTIONS:
            if data.get("sep"):
                toolbar.addSeparator()
                continue

            if data.get("is_tool_group"):
                self._add_tool_group(toolbar)
                continue

            action = self._create_action(data)
            toolbar.addAction(action)

        self.app_state.tool_changed.connect(self._update_active_tool_button)
        return toolbar

    def _add_tool_group(self, toolbar: QToolBar):
        tools_group = QActionGroup(self.main_window)
        tools_group.setExclusive(True)

        for tool_name, data in config.TOOLS.items():
            action_data = data.copy()
            action_data["checkable"] = True
            action_data["handler_name"] = \
                lambda \
                        checked, tool=tool_name: \
                    (self.app_state.set_tool(tool)) \
                    if checked else None

            action = self._create_action(action_data, tooltip_prefix=data.get("text", ""))
            tools_group.addAction(action)
            toolbar.addAction(action)
            self.tool_actions[tool_name] = action

    def _create_action(self, data: Dict[str, Any], tooltip_prefix: str = "") -> QAction:
        text = data.get("text", "")
        icon_path = data.get("icon", "")
        icon = QIcon(resource_path.get_resource_path(icon_path)) if icon_path else QIcon()

        action = QAction(icon, text, self.main_window)

        if "shortcut" in data:
            action.setShortcut(QKeySequence(data["shortcut"]))
        if "checkable" in data:
            action.setCheckable(True)
        if "checked" in data:
            action.setChecked(True)

        handler_name = data.get("handler_name")
        if handler_name:
            if callable(handler_name):
                action.triggered.connect(handler_name)
            elif handler_name in self.handlers:
                action.triggered.connect(self.handlers[handler_name])

        tooltip = data.get("tooltip", tooltip_prefix or text)
        shortcut_text = f" ({data['shortcut']})" if 'shortcut' in data else ""
        action.setToolTip(f"{tooltip}{shortcut_text}")

        return action

    def _update_active_tool_button(self, tool_name: str):
        if tool_name in self.tool_actions:
            self.tool_actions[tool_name].setChecked(True)