from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from model.memo import Memo
from model.task import Task
from ui.icons import asset_pixmap
from ui.page_utils import clear_layout, empty_label, make_scroll, section_label
from ui.styles import Theme
from ui.task_item import TaskItem


class TodayPage(QWidget):
    task_toggled = Signal(object, bool)
    edit_requested = Signal(object)
    delete_requested = Signal(object)
    report_toggled = Signal(object)
    result_requested = Signal(object)
    memo_open_requested = Signal(object)

    def __init__(self, theme: Theme, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._items: list[TaskItem] = []
        host = QWidget()
        self.list_layout = QVBoxLayout(host)
        self.list_layout.setContentsMargins(0, 0, 4, 0)
        self.list_layout.setSpacing(2)
        self.heading_icon = QLabel()
        self.heading_icon.setFixedSize(22, 22)
        self.heading_icon.setPixmap(asset_pixmap("nav_today", 22))
        self.heading = QLabel()
        self.heading.setStyleSheet("font-size: 18px; font-weight: 600;")
        head = QHBoxLayout()
        head.setContentsMargins(2, 0, 2, 0)
        head.setSpacing(8)
        head.addWidget(self.heading_icon)
        head.addWidget(self.heading, 1)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)
        root.addLayout(head)
        root.addWidget(make_scroll(host), 1)
        self.reload([], [])

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.heading.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {theme.text};")
        self.heading_icon.setPixmap(asset_pixmap("nav_today", 22))

    def flash_task(self, task_id: int) -> None:
        for item in self._items:
            if item.task.id == task_id:
                item.flash()
                break

    def reload(self, tasks: list[Task], memos: list[Memo]) -> None:
        today = datetime.now()
        self.heading.setText(today.strftime("今天 · %m月%d日"))
        pending = [
            task
            for task in tasks
            if not task.is_completed and (task.is_today() or task.is_overdue or task.due_time is None)
        ]
        completed = [task for task in tasks if task.is_completed and task.completed_at and task.completed_at.date() == today.date()]
        soon = today + timedelta(days=3)
        upcoming = [
            task
            for task in tasks
            if not task.is_completed
            and task.due_time
            and today.date() < task.due_time.date() <= soon.date()
        ]
        today_memos = [
            memo
            for memo in memos
            if (memo.updated_at and memo.updated_at.date() == today.date())
            or (memo.created_at and memo.created_at.date() == today.date())
        ]

        clear_layout(self.list_layout)
        self._items.clear()
        if not pending and not completed and not upcoming and not today_memos:
            self.list_layout.addWidget(empty_label("今天还很轻松，在下方记一件事吧", self._theme))
            self.list_layout.addStretch()
            return

        if pending:
            self.list_layout.addWidget(section_label(f"待完成  {len(pending)}", self._theme))
            for task in pending:
                self._add_task(task)
        if completed:
            self.list_layout.addWidget(section_label(f"今日已完成  {len(completed)}", self._theme))
            for task in completed:
                self._add_task(task)
        if upcoming:
            self.list_layout.addWidget(section_label(f"即将到期  {len(upcoming)}", self._theme))
            for task in upcoming:
                self._add_task(task)
        if today_memos:
            self.list_layout.addWidget(section_label(f"备忘记录  {len(today_memos)}", self._theme))
            for memo in today_memos:
                self._add_memo(memo)
        self.list_layout.addStretch()

    def _add_task(self, task: Task) -> None:
        item = TaskItem(task, self._theme)
        item.toggled.connect(self.task_toggled.emit)
        item.edit_requested.connect(self.edit_requested.emit)
        item.delete_requested.connect(self.delete_requested.emit)
        item.report_toggled.connect(self.report_toggled.emit)
        item.result_requested.connect(self.result_requested.emit)
        self.list_layout.addWidget(item)
        self._items.append(item)

    def _add_memo(self, memo: Memo) -> None:
        card = QLabel(memo.display_title())
        card.setWordWrap(True)
        card.setCursor(Qt.PointingHandCursor)
        card.setStyleSheet(
            f"background: {self._theme.surface}; border: 1px solid {self._theme.border};"
            f"border-radius: {self._theme.chip_radius}px; padding: 8px 10px;"
        )
        card.mousePressEvent = lambda event, item=memo: self.memo_open_requested.emit(item)  # type: ignore[method-assign]
        self.list_layout.addWidget(card)
