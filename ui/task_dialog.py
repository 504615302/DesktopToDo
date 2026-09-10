from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from model.task import Task
from ui.datetime_picker import Chip, DateTimePicker, IconButton
from ui.icons import stroke_icon
from ui.styles import Theme

REMINDER_CHOICES = [
    ("准时", 0),
    ("5 分钟", 5),
    ("10 分钟", 10),
    ("30 分钟", 30),
    ("1 小时", 60),
]
PRIORITY_CHOICES = [("低", 0), ("普通", 1), ("高", 2), ("紧急", 3)]
CATEGORY_CHOICES = ["工作", "生活", "学习", "其他"]


class TaskDialog(QDialog):
    def __init__(self, theme: Theme, task: Task | None = None, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._task = task
        self._priority = task.priority_enum.value if task else 1
        self._category = task.category if task else "工作"
        self._reminder_minutes = 0
        self._drag_offset: QPoint | None = None
        self.setWindowTitle("编辑任务" if task else "新建任务")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._build()
        if task:
            self.title_edit.setText(task.title)
            self.desc_edit.setPlainText(task.description)
            self._set_priority(task.priority_enum.value)
            self._set_category(task.category)
            self.report_check.setChecked(task.include_in_report)
            has_due = task.due_time is not None
            self.due_check.setChecked(has_due)
            self.remind_check.setChecked(has_due and task.reminder_minutes is not None)
            if task.due_time:
                self.picker.set_value(task.due_time)
            if task.reminder_minutes is not None:
                self._set_reminder_minutes(task.reminder_minutes)
        self._sync_reminder_inputs()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -8)
        path = QPainterPath()
        path.addRoundedRect(rect, self._theme.radius, self._theme.radius)
        painter.fillPath(path, QColor(self._theme.bg))
        painter.setPen(QColor(self._theme.border))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.LeftButton and self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(12)

        header = QHBoxLayout()
        heading = QLabel("编辑任务" if self._task else "新建任务")
        heading.setStyleSheet("font-size: 17px; font-weight: 600;")
        close_btn = IconButton("close", self._theme.text_muted, "关闭", 28, 14)
        close_btn.clicked.connect(self.reject)
        header.addWidget(heading)
        header.addStretch()
        header.addWidget(close_btn)
        layout.addLayout(header)

        layout.addWidget(self._caption("任务名称"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("输入任务名称")
        self.title_edit.setFixedHeight(40)
        layout.addWidget(self.title_edit)

        layout.addWidget(self._caption("任务描述"))
        self.desc_edit = QPlainTextEdit()
        self.desc_edit.setPlaceholderText("可选，补充说明")
        self.desc_edit.setFixedHeight(76)
        layout.addWidget(self.desc_edit)

        layout.addWidget(self._caption("优先级"))
        priority_row = QHBoxLayout()
        priority_row.setSpacing(8)
        self._priority_chips: list[Chip] = []
        for text, value in PRIORITY_CHOICES:
            chip = Chip(text, self._theme)
            chip.clicked.connect(lambda _=False, item=value: self._set_priority(item))
            self._priority_chips.append(chip)
            priority_row.addWidget(chip)
        priority_row.addStretch()
        layout.addLayout(priority_row)
        self._set_priority(self._priority)

        layout.addWidget(self._caption("分类"))
        category_row = QHBoxLayout()
        category_row.setSpacing(6)
        self._category_chips: list[Chip] = []
        for name in CATEGORY_CHOICES:
            chip = Chip(name, self._theme)
            chip.clicked.connect(lambda _=False, item=name: self._set_category(item))
            self._category_chips.append(chip)
            category_row.addWidget(chip)
        layout.addLayout(category_row)

        self.report_check = QCheckBox("加入周报素材")
        self.report_check.setChecked(True)
        layout.addWidget(self.report_check)
        self._set_category(self._category)

        self.due_check = QCheckBox("设置截止时间")
        self.due_check.toggled.connect(self._sync_reminder_inputs)
        layout.addWidget(self.due_check)

        self.picker = DateTimePicker(self._theme)
        layout.addWidget(self.picker)

        remind_row = QHBoxLayout()
        bell = QLabel()
        bell.setPixmap(stroke_icon("bell", self._theme.text_secondary, 16).pixmap(16, 16))
        remind_row.addWidget(bell)
        self.remind_check = QCheckBox("定时提醒")
        self.remind_check.toggled.connect(self._sync_reminder_inputs)
        remind_row.addWidget(self.remind_check)
        remind_row.addStretch()
        layout.addLayout(remind_row)

        layout.addWidget(self._caption("提醒方式"))
        offset_row = QHBoxLayout()
        offset_row.setSpacing(6)
        self._offset_chips: list[Chip] = []
        self._offset_values: list[int] = []
        for text, minutes in REMINDER_CHOICES:
            chip = Chip(text, self._theme)
            chip.clicked.connect(lambda _=False, item=minutes: self._set_reminder_minutes(item))
            self._offset_chips.append(chip)
            self._offset_values.append(minutes)
            offset_row.addWidget(chip)
        layout.addLayout(offset_row)
        self._set_reminder_minutes(0)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("取消")
        save = QPushButton("保存")
        save.setObjectName("primaryButton")
        save.setFixedHeight(36)
        cancel.setFixedHeight(36)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)
        self.title_edit.setFocus()

    def _caption(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"color: {self._theme.text_secondary}; font-size: 12px; font-weight: 600;")
        return label

    def _set_priority(self, value: int) -> None:
        self._priority = value
        for index, chip in enumerate(self._priority_chips):
            chip.setChecked(index == value)

    def _set_reminder_minutes(self, value: int) -> None:
        self._reminder_minutes = value
        for chip, minutes in zip(self._offset_chips, self._offset_values):
            chip.setChecked(minutes == value)

    def _sync_reminder_inputs(self) -> None:
        has_due = self.due_check.isChecked()
        self.picker.setEnabled(has_due)
        if not has_due:
            self.remind_check.setChecked(False)
        self.remind_check.setEnabled(has_due)
        remind = has_due and self.remind_check.isChecked()
        for chip in self._offset_chips:
            chip.setEnabled(remind)

    def _set_category(self, value: str) -> None:
        self._category = value
        for chip in self._category_chips:
            chip.setChecked(chip.text() == value)
        if not self._task:
            self.report_check.setChecked(value != "生活")

    def result_values(self) -> dict:
        due_time = self.picker.value() if self.due_check.isChecked() else None
        reminder_minutes = None
        if due_time is not None and self.remind_check.isChecked():
            reminder_minutes = self._reminder_minutes
        return {
            "title": self.title_edit.text().strip(),
            "description": self.desc_edit.toPlainText().strip(),
            "priority": self._priority,
            "due_time": due_time,
            "reminder_minutes": reminder_minutes,
            "category": self._category,
            "include_in_report": self.report_check.isChecked(),
        }
