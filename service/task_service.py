from __future__ import annotations

from datetime import datetime

from database.task_repository import TaskRepository
from model.task import Task, TaskStatus


class TaskService:
    def __init__(self, repository: TaskRepository):
        self._repo = repository

    def list_tasks(self) -> list[Task]:
        return self._repo.list_all()

    def add_task(self, title: str, description: str = "", priority: int = 0) -> Task:
        title = title.strip()
        if not title:
            raise ValueError("任务标题不能为空")
        task = Task(
            title=title,
            description=description.strip(),
            priority=priority,
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
