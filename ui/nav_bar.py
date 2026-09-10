from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from ui.page_utils import style_chip
from ui.styles import Theme

PAGES = [
    ("today", "今日"),
    ("todo", "Todo"),
    ("memo", "备忘录"),
    ("report", "周报"),
]


class NavBar(QWidget):
    page_changed = Signal(str)

    def __init__(self, theme: Theme, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._current = "today"
        self._buttons: dict[str, QPushButton] = {}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        for key, label in PAGES:
            button = QPushButton(label)
            button.setCursor(Qt.PointingHandCursor)
            button.setCheckable(True)
            button.setFixedHeight(30)
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
        self.refresh()

    def refresh(self) -> None:
        for key, button in self._buttons.items():
            style_chip(button, self._theme, key == self._current)
