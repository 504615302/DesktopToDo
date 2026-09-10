from __future__ import annotations

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QToolButton, QWidget

from ui.icons import stroke_icon
from ui.styles import Theme


class IconButton(QToolButton):
    def __init__(self, kind: str, color: str, tooltip: str, parent=None):
        super().__init__(parent)
        self._kind = kind
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setAutoRaise(True)
        self.setFixedSize(28, 28)
        self.setIconSize(QSize(16, 16))
        self.set_color(color)
        self.setStyleSheet(
            """
            QToolButton {
                border: none;
                border-radius: 8px;
                background: transparent;
                padding: 0;
            }
            QToolButton:hover {
                background: rgba(127, 127, 127, 40);
            }
            """
        )

    def set_color(self, color: str) -> None:
        self.setIcon(stroke_icon(self._kind, color, 16))

    def set_kind(self, kind: str, color: str) -> None:
        self._kind = kind
        self.set_color(color)


class TitleBar(QWidget):
    settings_clicked = Signal()
    pin_clicked = Signal()
    minimize_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, theme: Theme, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._drag_offset: QPoint | None = None
        self.setFixedHeight(44)
        self._title = QLabel("我的待办")
        self._title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {theme.text};")
        self._date = QLabel()
        self._date.setStyleSheet(f"font-size: 12px; color: {theme.text_secondary};")

        self.pin_btn = IconButton("pin", theme.text_secondary, "置顶")
        self.settings_btn = IconButton("settings", theme.text_secondary, "设置")
        self.min_btn = IconButton("minimize", theme.text_secondary, "最小化")
        self.close_btn = IconButton("close", theme.text_secondary, "关闭到托盘")

        self.pin_btn.clicked.connect(self.pin_clicked.emit)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        self.min_btn.clicked.connect(self.minimize_clicked.emit)
        self.close_btn.clicked.connect(self.close_clicked.emit)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 2, 0)
        layout.setSpacing(4)
        layout.addWidget(self._title)
        layout.addStretch()
        layout.addWidget(self._date)
        layout.addWidget(self.pin_btn)
        layout.addWidget(self.settings_btn)
        layout.addWidget(self.min_btn)
        layout.addWidget(self.close_btn)
        self._title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def set_date(self, text: str) -> None:
        self._date.setText(text)

    def set_pinned(self, pinned: bool) -> None:
        kind = "pinned" if pinned else "pin"
        self.pin_btn.set_kind(kind, self._theme.accent if pinned else self._theme.text_secondary)
        self.pin_btn.setToolTip("取消置顶" if pinned else "置顶")

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {theme.text};")
        self._date.setStyleSheet(f"font-size: 12px; color: {theme.text_secondary};")
        self.settings_btn.set_color(theme.text_secondary)
        self.min_btn.set_color(theme.text_secondary)
        self.close_btn.set_color(theme.text_secondary)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.LeftButton and self._drag_offset is not None:
            self.window().move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)
