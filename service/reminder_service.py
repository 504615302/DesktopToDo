from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal

from model.task import Task
from service.task_service import TaskService


class ReminderService(QObject):
    triggered = Signal(object)

    def __init__(self, task_service: TaskService, parent=None):
        super().__init__(parent)
        self._task_service = task_service
        self._timer = QTimer(self)
        self._timer.setInterval(8000)
        self._timer.timeout.connect(self.check)
        self._timer.start()
        QTimer.singleShot(1200, self.check)

    def check(self) -> None:
        for task in self._task_service.due_reminders():
            self._task_service.mark_reminded(task)
            self.triggered.emit(task)
