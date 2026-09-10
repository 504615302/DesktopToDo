from __future__ import annotations

from datetime import datetime
from typing import Optional

from database.task_repository import TaskRepository
from model.task import Priority, Task, TaskStatus


class TaskService:
    def __init__(self, repository: TaskRepository):
        self._repo = repository

    def list_tasks(self) -> list[Task]:
        return self._repo.list_all()

    def add_task(self, title: str, description: str = "", priority: int | None = None, category: str = "工作") -> Task:
        title = title.strip()
        if not title:
            raise ValueError("任务标题不能为空")
        include = category != "生活"
        task = Task(
            title=title,
            description=description.strip(),
            priority=Priority.NORMAL if priority is None else priority,
            category=category,
            include_in_report=include,
            sort_order=self._repo.min_sort_order() - 1,
            created_at=datetime.now(),
        )
        return self._repo.add(task)

    def update_task(self, task: Task) -> Task:
        task.title = task.title.strip()
        if not task.title:
            raise ValueError("任务标题不能为空")
        return self._repo.update(task)

    def delete_task(self, task_id: int) -> None:
        self._repo.delete(task_id)

    def set_completed(self, task: Task, completed: bool) -> Task:
        if completed:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
        else:
            task.status = TaskStatus.PENDING
            task.completed_at = None
        return self._repo.update(task)

    def due_reminders(self, now: Optional[datetime] = None) -> list[Task]:
        now = now or datetime.now()
        ready: list[Task] = []
        for task in self.list_tasks():
            fire_at = task.reminder_at()
            if task.is_completed or fire_at is None or task.reminded_at:
                continue
            if now >= fire_at:
                ready.append(task)
        return ready

    def mark_reminded(self, task: Task) -> Task:
        task.reminded_at = datetime.now()
        return self._repo.update(task)

    def search(self, keyword: str) -> list[Task]:
        key = keyword.strip().lower()
        if not key:
            return self.list_tasks()
        result = []
        for task in self.list_tasks():
            hay = f"{task.title} {task.description} {task.category}".lower()
            if key in hay:
                result.append(task)
        return result
