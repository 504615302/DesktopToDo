from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from model.task import Priority, Task
from ui.icons import stroke_icon
from ui.styles import Theme


class CheckMark(QWidget):
    toggled = Signal(bool)

    def __init__(self, checked: bool, theme: Theme, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._theme = theme
        self.setFixedSize(20, 20)
        self.setCursor(Qt.PointingHandCursor)

    def set_checked(self, checked: bool) -> None:
        self._checked = checked
        self.update()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked
            self.toggled.emit(self._checked)
            self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(1.5, 1.5, 17, 17)
        if self._checked:
            painter.setBrush(QColor(self._theme.accent))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 5, 5)
            pen = QPen(QColor("#FFFFFF"), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(5, 10, 8, 13)
            painter.drawLine(8, 13, 14, 7)
        else:
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(self._theme.border), 1.4))
            painter.drawRoundedRect(rect, 5, 5)


class TaskItem(QWidget):
    toggled = Signal(object, bool)
    edit_requested = Signal(object)
    delete_requested = Signal(object)

    def __init__(self, task: Task, theme: Theme, parent=None):
        super().__init__(parent)
        self.task = task
        self._theme = theme
        self.setObjectName("taskItem")
        self.setMinimumHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self._build()
        self._refresh()

    def _build(self) -> None:
        self.check = CheckMark(self.task.is_completed, self._theme)
        self.check.toggled.connect(lambda checked: self.toggled.emit(self.task, checked))

        self.title = QLabel()
        self.title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.title.setMinimumWidth(40)
        self.desc = QLabel()
        self.desc.setWordWrap(False)
        self.desc.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.desc.setMinimumWidth(40)

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(0)
        text_box.addWidget(self.title)
        text_box.addWidget(self.desc)

        self.priority = QLabel()
        self.priority.setFixedWidth(22)
        self.priority.setAlignment(Qt.AlignCenter)

        self.edit_btn = QToolButton()
        self.delete_btn = QToolButton()
        for button, kind, tip, handler in (
            (self.edit_btn, "edit", "编辑", lambda: self.edit_requested.emit(self.task)),
            (self.delete_btn, "delete", "删除", lambda: self.delete_requested.emit(self.task)),
        ):
            button.setAutoRaise(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setToolTip(tip)
            button.setFixedSize(24, 24)
            button.setIcon(stroke_icon(kind, self._theme.text_secondary, 14))
            button.clicked.connect(handler)
            button.hide()
            button.setStyleSheet("QToolButton { border: none; border-radius: 6px; }")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 6, 6)
        layout.setSpacing(8)
        layout.addWidget(self.check, 0, Qt.AlignTop)
        layout.addLayout(text_box, 1)
        layout.addWidget(self.priority)
        layout.addWidget(self.edit_btn)
        layout.addWidget(self.delete_btn)

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.check.apply_theme(theme)
        self.edit_btn.setIcon(stroke_icon("edit", theme.text_secondary, 14))
        self.delete_btn.setIcon(stroke_icon("delete", theme.text_secondary, 14))
        self._refresh()

    def set_task(self, task: Task) -> None:
        self.task = task
        self.check.set_checked(task.is_completed)
        self._refresh()

    def _refresh(self) -> None:
        completed = self.task.is_completed
        color = self._theme.completed if completed else self._theme.text
        font = QFont()
        font.setStrikeOut(completed)
        font.setPointSize(10)
        self.title.setFont(font)
        self.title.setText(self.task.title)
        self.title.setStyleSheet(f"color: {color};")

        if self.task.description and not completed:
            self.desc.setText(self.task.description.replace("\n", " "))
            self.desc.setStyleSheet(f"color: {self._theme.text_muted}; font-size: 11px;")
            self.desc.show()
        else:
            self.desc.hide()

        icon = self.task.priority_enum.icon
        self.priority.setText(icon)
        self.priority.setVisible(bool(icon) and not completed)
        self._update_background(False)

    def _update_background(self, hovered: bool) -> None:
        bg = self._theme.hover if hovered else "transparent"
        self.setStyleSheet(f"#taskItem {{ background: {bg}; border-radius: 8px; }}")

    def enterEvent(self, event) -> None:
        self.edit_btn.show()
        self.delete_btn.show()
        self._update_background(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.edit_btn.hide()
        self.delete_btn.hide()
        self._update_background(False)
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.edit_requested.emit(self.task)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除任务")
        chosen = menu.exec(event.globalPos())
        if chosen is edit_action:
            self.edit_requested.emit(self.task)
        elif chosen is delete_action:
            self.delete_requested.emit(self.task)
