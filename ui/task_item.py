from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from model.task import Task
from ui.datetime_picker import IconButton
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
            painter.drawRoundedRect(rect, self._theme.check_radius, self._theme.check_radius)
            pen = QPen(QColor("#FFFFFF"), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(5, 10, 8, 13)
            painter.drawLine(8, 13, 14, 7)
        else:
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(self._theme.border), 1.4))
            painter.drawRoundedRect(rect, self._theme.check_radius, self._theme.check_radius)


class TaskItem(QWidget):
    toggled = Signal(object, bool)
    edit_requested = Signal(object)
    delete_requested = Signal(object)
    report_toggled = Signal(object)
    result_requested = Signal(object)

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
        self.priority.setFixedSize(18, 18)
        self.priority.setAlignment(Qt.AlignCenter)

        self.due_icon = QLabel()
        self.due_icon.setFixedSize(14, 14)
        self.due = QLabel()
        self.due.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.edit_btn = IconButton("edit", self._theme.text_secondary, "编辑", 26, 14)
        self.delete_btn = IconButton("delete", self._theme.danger, "删除", 26, 14)
        self.edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.task))
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.task))
        self.edit_btn.hide()
        self.delete_btn.hide()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 6, 8)
        layout.setSpacing(8)
        layout.addWidget(self.check, 0, Qt.AlignVCenter)
        layout.addLayout(text_box, 1)
        layout.addWidget(self.due_icon)
        layout.addWidget(self.due)
        layout.addWidget(self.priority)
        layout.addWidget(self.edit_btn)
        layout.addWidget(self.delete_btn)

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.check.apply_theme(theme)
        self.edit_btn.set_color(theme.text_secondary)
        self.delete_btn.set_color(theme.danger)
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

        level = self.task.priority_enum.value
        if not completed and level >= 2:
            color = self._theme.danger if level >= 3 else self._theme.accent
            self.priority.setPixmap(stroke_icon("flag", color, 14).pixmap(14, 14))
            self.priority.show()
        else:
            self.priority.hide()

        due_text = self.task.due_label()
        due_color = self._theme.danger if self.task.is_overdue else self._theme.text_secondary
        self.due.setText(due_text)
        self.due.setStyleSheet(f"color: {due_color}; font-size: 11px;")
        visible_due = bool(due_text) and not completed
        self.due.setVisible(visible_due)
        if visible_due:
            self.due_icon.setPixmap(stroke_icon("calendar", due_color, 13).pixmap(13, 13))
        self.due_icon.setVisible(visible_due)
        self._update_background(False)

    def _update_background(self, hovered: bool) -> None:
        bg = self._theme.hover if hovered else "transparent"
        self.setStyleSheet(
            f"#taskItem {{ background: {bg}; border-radius: {self._theme.chip_radius}px; }}"
        )

    def flash(self) -> None:
        start = QColor(self._theme.accent)
        start.setAlpha(70)
        end = QColor("transparent")
        anim = QVariantAnimation(self)
        anim.setDuration(1400)
        anim.setKeyValueAt(0.0, start)
        anim.setKeyValueAt(0.35, end)
        anim.setKeyValueAt(0.55, start)
        anim.setKeyValueAt(1.0, end)
        anim.valueChanged.connect(self._on_flash_color)
        anim.finished.connect(lambda: self._update_background(False))
        anim.start()
        self._flash_anim = anim

    def _on_flash_color(self, color) -> None:
        if isinstance(color, QColor):
            self.setStyleSheet(
                f"#taskItem {{ background: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()}); "
                f"border-radius: {self._theme.chip_radius}px; }}"
            )

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
        result_action = menu.addAction("记录工作结果")
        report_action = menu.addAction("从周报素材移除" if self.task.include_in_report else "加入本周周报")
        delete_action = menu.addAction("删除任务")
        chosen = menu.exec(event.globalPos())
        if chosen is edit_action:
            self.edit_requested.emit(self.task)
        elif chosen is result_action:
            self.result_requested.emit(self.task)
        elif chosen is report_action:
            self.report_toggled.emit(self.task)
        elif chosen is delete_action:
            self.delete_requested.emit(self.task)
