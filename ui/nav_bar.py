from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QToolButton, QWidget

from ui.icons import asset_icon, stroke_icon
from ui.page_utils import style_nav_button
from ui.styles import Theme

PAGES = [
    ("today", "今日", "nav_today"),
    ("todo", "Todo", "nav_todo"),
    ("memo", "备忘", "nav_memo"),
    ("report", "周报", "nav_report"),
    ("chat", "问答", "nav_chat"),
    ("tools", "工具", "nav_tools"),
]


class NavBar(QWidget):
    page_changed = Signal(str)

    def __init__(self, theme: Theme, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._current = "today"
        self._buttons: dict[str, QToolButton] = {}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        for key, label, icon_name in PAGES:
            button = QToolButton()
            button.setCursor(Qt.PointingHandCursor)
            button.setCheckable(True)
            button.setAutoRaise(True)
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setIconSize(QSize(20, 20))
            button.setIcon(self._page_icon(icon_name))
            button.setText(label)
            button.setToolTip(label)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setFixedHeight(48)
            button.clicked.connect(lambda _=False, value=key: self.set_page(value, emit=True))
            layout.addWidget(button, 1)
            self._buttons[key] = button
        self.refresh()

    def set_page(self, key: str, emit: bool = False) -> None:
        if key not in self._buttons:
            key = "today"
        self._current = key
        self.refresh()
        if emit:
            self.page_changed.emit(key)

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        for key, _label, icon_name in PAGES:
            self._buttons[key].setIcon(self._page_icon(icon_name))
        self.refresh()

    def _page_icon(self, name: str):
        icon = asset_icon(name, 20)
        if not icon.isNull():
            return icon
        fallback = {"nav_chat": "chat", "nav_tools": "wrench", "nav_memo": "note", "nav_report": "calendar"}
        return stroke_icon(fallback.get(name, "sparkle"), self._theme.accent, 20)

    def refresh(self) -> None:
        for key, button in self._buttons.items():
            style_nav_button(button, self._theme, key == self._current)
