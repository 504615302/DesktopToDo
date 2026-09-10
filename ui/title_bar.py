from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QSizePolicy, QWidget

from ui.datetime_picker import IconButton
from ui.styles import THEME_CHOICES, Theme


class TitleBar(QWidget):
    settings_clicked = Signal()
    lock_clicked = Signal()
    pin_clicked = Signal()
    theme_selected = Signal(str)
    minimize_clicked = Signal()
    compact_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, theme: Theme, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._locked = False
        self._pinned = False
        self._compact = False
        self._drag_offset: QPoint | None = None
        self.setFixedHeight(44)
        self._title = QLabel(theme.title)
        self._title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {theme.text};")

        self.lock_btn = IconButton("unlock", theme.text_secondary, "锁定位置")
        self.pin_btn = IconButton("pin", theme.text_secondary, "窗口置顶")
        self.theme_btn = IconButton("theme", theme.text_secondary, "切换主题")
        self.settings_btn = IconButton("settings", theme.text_secondary, "设置")
        self.min_btn = IconButton("minimize", theme.text_secondary, "最小化")
        self.compact_btn = IconButton("collapse", theme.text_secondary, "折叠为问答")
        self.close_btn = IconButton("close", theme.text_secondary, "关闭到托盘")

        self.lock_btn.clicked.connect(self.lock_clicked.emit)
        self.pin_btn.clicked.connect(self.pin_clicked.emit)
        self.theme_btn.clicked.connect(self._open_theme_menu)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        self.min_btn.clicked.connect(self.minimize_clicked.emit)
        self.compact_btn.clicked.connect(self.compact_clicked.emit)
        self.close_btn.clicked.connect(self.close_clicked.emit)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self._title)
        layout.addStretch()
        layout.addWidget(self.pin_btn)
        layout.addWidget(self.theme_btn)
        layout.addWidget(self.settings_btn)
        layout.addWidget(self.lock_btn)
        layout.addWidget(self.min_btn)
        layout.addWidget(self.compact_btn)
        layout.addWidget(self.close_btn)
        self._title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def set_date(self, text: str) -> None:
        self._title.setToolTip(text)

    def set_locked(self, locked: bool) -> None:
        self._locked = locked
        kind = "lock" if locked else "unlock"
        color = self._theme.accent if locked else self._theme.text_secondary
        self.lock_btn.set_kind(kind, color)
        self.lock_btn.setToolTip("解锁位置" if locked else "锁定位置")

    def set_pinned(self, pinned: bool) -> None:
        self._pinned = pinned
        kind = "pinned" if pinned else "pin"
        color = self._theme.accent if pinned else self._theme.text_secondary
        self.pin_btn.set_kind(kind, color)
        self.pin_btn.setToolTip("取消置顶" if pinned else "窗口置顶")

    def set_compact(self, compact: bool) -> None:
        self._compact = compact
        self._title.setText("问答" if compact else self._theme.title)
        for button in (self.theme_btn, self.settings_btn, self.lock_btn, self.min_btn):
            button.setVisible(not compact)
        kind = "expand" if compact else "collapse"
        color = self._theme.accent if compact else self._theme.text_secondary
        self.compact_btn.set_kind(kind, color)
        self.compact_btn.setToolTip("展开窗口" if compact else "折叠为问答")

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {theme.text};")
        if not self._compact:
            self._title.setText(theme.title)
        self.theme_btn.set_color(theme.text_secondary)
        self.settings_btn.set_color(theme.text_secondary)
        self.min_btn.set_color(theme.text_secondary)
        self.close_btn.set_color(theme.text_secondary)
        self.set_locked(self._locked)
        self.set_pinned(self._pinned)
        self.set_compact(self._compact)

    def _open_theme_menu(self) -> None:
        menu = QMenu(self)
        for label, value in THEME_CHOICES:
            action = menu.addAction(label)
            action.setData(value)
        chosen = menu.exec(self.theme_btn.mapToGlobal(self.theme_btn.rect().bottomLeft()))
        if chosen is not None:
            self.theme_selected.emit(str(chosen.data()))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and not self._locked:
            self._drag_offset = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.LeftButton and self._drag_offset is not None and not self._locked:
            self.window().move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)
