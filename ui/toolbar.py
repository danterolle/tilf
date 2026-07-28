from collections.abc import Callable, Mapping

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QActionGroup, QIcon, QKeySequence
from PySide6.QtWidgets import QMainWindow, QToolBar

from state import AppState
from utils import config, resource_path
from utils.toolbar_config import ToolbarAction


class Toolbar:
    def __init__(self, main_window: QMainWindow, app_state: AppState, handlers: Mapping[str, Callable[..., object]]):
        self.main_window = main_window
        self.app_state = app_state
        self.handlers = handlers
        self.tool_actions: dict[str, QAction] = {}
        self.actions_by_handler: dict[str, QAction] = {}

    def create_toolbar(self) -> QToolBar:
        toolbar = QToolBar(config.TOOLBAR_TITLE)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setMovable(False)

        for data in config.TOOLBAR_ACTIONS:
            if data.separator:
                toolbar.addSeparator()
                continue

            if data.tool_group:
                self._add_tool_group(toolbar)
                continue

            action = self._create_action(data)
            toolbar.addAction(action)

        self.app_state.tool_changed.connect(self._update_active_tool_button)
        return toolbar

    def _add_tool_group(self, toolbar: QToolBar) -> None:
        tools_group = QActionGroup(self.main_window)
        tools_group.setExclusive(True)

        for tool_name, data in config.TOOLS.items():
            action_data = ToolbarAction(
                text=data.text,
                icon=data.icon,
                shortcut=data.shortcut,
                tooltip=data.tooltip,
                checkable=True,
            )

            action = self._create_action(action_data, tooltip_prefix=data.text)
            action.triggered.connect(
                lambda checked, tool=tool_name: self.app_state.set_tool(tool) if checked else None
            )
            tools_group.addAction(action)
            toolbar.addAction(action)
            self.tool_actions[tool_name] = action

    def _create_action(self, data: ToolbarAction, tooltip_prefix: str = "") -> QAction:
        text = data.text
        icon_path = data.icon
        icon = QIcon(resource_path.get_resource_path(icon_path)) if icon_path else QIcon()

        action = QAction(icon, text, self.main_window)

        if data.shortcut:
            action.setShortcut(QKeySequence(data.shortcut))
        if data.checkable:
            action.setCheckable(True)
        if data.checked:
            action.setChecked(True)

        handler_name = data.handler_name
        if handler_name:
            if handler_name in self.handlers:
                action.triggered.connect(self.handlers[handler_name])
                self.actions_by_handler[handler_name] = action

        tooltip = data.tooltip or tooltip_prefix or text
        shortcut_text = f" ({data.shortcut})" if data.shortcut else ""
        action.setToolTip(f"{tooltip}{shortcut_text}")

        return action

    def _update_active_tool_button(self, tool_name: str) -> None:
        if tool_name in self.tool_actions:
            self.tool_actions[tool_name].setChecked(True)

    def action_for_handler(self, handler_name: str) -> QAction | None:
        return self.actions_by_handler.get(handler_name)
