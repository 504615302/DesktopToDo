from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

from model.task import Task
from ui.page_utils import clear_layout, empty_label, make_scroll, section_label, style_chip
from ui.styles import Theme
from ui.task_item import TaskItem

FILTERS = [
    ("today", "今天"),
    ("all", "全部"),
    ("incomplete", "未完成"),
    ("completed", "已完成"),
    ("overdue", "逾期"),
]


class TodoPage(QWidget):
    task_toggled = Signal(object, bool)
    edit_requested = Signal(object)
    delete_requested = Signal(object)
    report_toggled = Signal(object)
    result_requested = Signal(object)
    filter_changed = Signal(str)

    def __init__(self, theme: Theme, filter_mode: str = "today", parent=None):
        super().__init__(parent)
        self._theme = theme
        self._filter = filter_mode if filter_mode in {key for key, _ in FILTERS} else "today"
        self._keyword = ""
        self._items: list[TaskItem] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索标题、描述、分类")
        self.search.setFixedHeight(34)
        self.search.textChanged.connect(self._on_search)

        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(6)
        self._filter_buttons: dict[str, QPushButton] = {}
        for key, label in FILTERS:
            button = QPushButton(label)
            button.setCursor(Qt.PointingHandCursor)
            button.setCheckable(True)
            button.clicked.connect(lambda _=False, value=key: self.set_filter(value))
            filter_row.addWidget(button)
            self._filter_buttons[key] = button
        filter_row.addStretch()

        host = QWidget()
        self.list_layout = QVBoxLayout(host)
        self.list_layout.setContentsMargins(0, 0, 4, 0)
        self.list_layout.setSpacing(2)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        root.addWidget(self.search)
        root.addLayout(filter_row)
        root.addWidget(make_scroll(host), 1)
        self._refresh_filters()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._refresh_filters()

    def set_filter(self, mode: str) -> None:
        self._filter = mode
        self._refresh_filters()
        self.filter_changed.emit(mode)

    def flash_task(self, task_id: int) -> None:
        for item in self._items:
            if item.task.id == task_id:
                item.flash()
                break

    def reload(self, tasks: list[Task]) -> None:
        key = self._keyword.lower()
        if key:
            tasks = [
                task
                for task in tasks
                if key in f"{task.title} {task.description} {task.category}".lower()
            ]
        pending = [task for task in tasks if not task.is_completed]
        completed = [task for task in tasks if task.is_completed]
        mode = self._filter
        if mode == "today":
            pending = [task for task in pending if task.is_today() or task.is_overdue]
            completed = [task for task in completed if task.is_today()]
        elif mode == "incomplete":
            completed = []
        elif mode == "completed":
            pending = []
        elif mode == "overdue":
            pending = [task for task in pending if task.is_overdue]
            completed = []

        clear_layout(self.list_layout)
        self._items.clear()
        if not pending and not completed:
            self.list_layout.addWidget(empty_label("暂无待办，在下方输入后按 Enter 添加", self._theme))
            self.list_layout.addStretch()
            return
        if pending:
            self.list_layout.addWidget(section_label(f"未完成  {len(pending)}", self._theme))
            for task in pending:
                self._add_item(task)
        if completed:
            self.list_layout.addWidget(section_label(f"已完成  {len(completed)}", self._theme))
            for task in completed:
                self._add_item(task)
        self.list_layout.addStretch()

    def _add_item(self, task: Task) -> None:
        item = TaskItem(task, self._theme)
        item.toggled.connect(self.task_toggled.emit)
        item.edit_requested.connect(self.edit_requested.emit)
        item.delete_requested.connect(self.delete_requested.emit)
        item.report_toggled.connect(self.report_toggled.emit)
        item.result_requested.connect(self.result_requested.emit)
        self.list_layout.addWidget(item)
        self._items.append(item)

    def _on_search(self, text: str) -> None:
        self._keyword = text
        self.filter_changed.emit(self._filter)

    def _refresh_filters(self) -> None:
        for key, button in self._filter_buttons.items():
            style_chip(button, self._theme, key == self._filter)
