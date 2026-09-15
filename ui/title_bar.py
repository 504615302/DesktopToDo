from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QSizePolicy, QWidget

from ui.datetime_picker import IconButton
from ui.styles import THEME_CHOICES, Theme

TITLE_BTN = 36
TITLE_ICON = 20


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
        self.setObjectName("titleBar")
        self._theme = theme
        self._locked = False
        self._pinned = False
        self._compact = False
        self._drag_offset: QPoint | None = None
        self.setMinimumHeight(48)
        self.setFixedHeight(48)
        self._title = QLabel(theme.title)
        self._title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {theme.text};")

        self.lock_btn = IconButton("unlock", theme.text_secondary, "锁定位置", TITLE_BTN, TITLE_ICON)
        self.pin_btn = IconButton("sf-pin", theme.text_secondary, "窗口置顶", TITLE_BTN, TITLE_ICON)
        self.theme_btn = IconButton("sf-palette", theme.text_secondary, "切换主题", TITLE_BTN, TITLE_ICON)
        self.settings_btn = IconButton("sf-sliders", theme.text_secondary, "设置", TITLE_BTN, TITLE_ICON)
        for button in (self.pin_btn, self.theme_btn, self.settings_btn):
            button.setObjectName("titleUtilityButton")
        self.min_btn = IconButton("minimize", theme.text_secondary, "最小化", TITLE_BTN, TITLE_ICON)
        self.compact_btn = IconButton("collapse", theme.text_secondary, "折叠为问答", TITLE_BTN, TITLE_ICON)
        self.close_btn = IconButton("close", theme.text_secondary, "关闭到托盘", TITLE_BTN, TITLE_ICON)

        self.lock_btn.clicked.connect(self.lock_clicked.emit)
        self.pin_btn.clicked.connect(self.pin_clicked.emit)
        self.theme_btn.clicked.connect(self._open_theme_menu)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        self.min_btn.clicked.connect(self.minimize_clicked.emit)
        self.compact_btn.clicked.connect(self.compact_clicked.emit)
        self.close_btn.clicked.connect(self.close_clicked.emit)

        self.product_actions = QWidget()
        self.product_actions.setObjectName("productActions")
        product_layout = QHBoxLayout(self.product_actions)
        product_layout.setContentsMargins(0, 0, 0, 0)
        product_layout.setSpacing(0)
        for button in (self.pin_btn, self.theme_btn, self.settings_btn, self.lock_btn):
            product_layout.addWidget(button)

        self.window_actions = QWidget()
        self.window_actions.setObjectName("windowActions")
        window_layout = QHBoxLayout(self.window_actions)
        window_layout.setContentsMargins(4, 0, 0, 0)
        window_layout.setSpacing(0)
        for button in (self.min_btn, self.compact_btn, self.close_btn):
            window_layout.addWidget(button)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 2, 4)
        layout.setSpacing(6)
        layout.addWidget(self._title)
        layout.addStretch()
        layout.addWidget(self.product_actions)
        layout.addWidget(self.window_actions)
        self._title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.apply_theme(theme)

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
        kind = "sf-pin-fill" if pinned else "sf-pin"
        color = self._theme.accent if pinned else self._theme.text_secondary
        self.pin_btn.set_kind(kind, color)
        self.pin_btn.setToolTip("取消置顶" if pinned else "窗口置顶")
        self._style_utility_buttons()

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
        self.setStyleSheet(
            f"#titleBar {{ background: transparent; }} "
            f"#productActions {{ background: {theme.chrome}; border: 1px solid {theme.separator}; "
            f"border-radius: 18px; padding: 1px; }} "
            f"#windowActions {{ border-left: 1px solid {theme.separator}; }}"
        )
        self._style_utility_buttons()

    def _style_utility_buttons(self) -> None:
        for button, active in (
            (self.pin_btn, self._pinned),
            (self.theme_btn, False),
            (self.settings_btn, False),
        ):
            button.setStyleSheet(
                f"""
                QToolButton#titleUtilityButton {{
                    background: {self._theme.accent_soft if active else 'transparent'};
                    border: 1px solid {self._theme.accent if active else 'transparent'};
                    border-radius: 16px;
                    padding: 0;
                }}
                QToolButton#titleUtilityButton:hover {{ background: {self._theme.hover}; }}
                QToolButton#titleUtilityButton:pressed {{ background: {self._theme.accent_soft}; }}
                QToolButton#titleUtilityButton:focus {{ border: 2px solid {self._theme.focus_ring}; }}
                """
            )

    def _open_theme_menu(self) -> None:
        menu = QMenu(self)
        menu.addSection("主题风格")
        for label, value in THEME_CHOICES:
            action = menu.addAction(label)
            action.setData(value)
            action.setCheckable(True)
            action.setChecked(value == self._theme.name)
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
