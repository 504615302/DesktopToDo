from __future__ import annotations

from datetime import datetime
from typing import Optional

from database.common import dump_dt, parse_dt, row_value
from model.task import Task, TaskStatus


def _row_to_task(row) -> Task:
    reminder = row_value(row, "reminder_minutes")
    include = row_value(row, "include_in_report", 1)
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"] or "",
        status=row["status"] or 0,
        priority=row["priority"] if row["priority"] is not None else 1,
        due_time=parse_dt(row["due_time"]),
        reminder_minutes=None if reminder is None else int(reminder),
        reminded_at=parse_dt(row_value(row, "reminded_at")),
        completed_at=parse_dt(row["completed_at"]),
        sort_order=row["sort_order"] or 0,
        created_at=parse_dt(row["created_at"]),
        updated_at=parse_dt(row["updated_at"]),
        category=row_value(row, "category", "工作") or "工作",
        include_in_report=bool(int(include) if include is not None else 1),
    )


class TaskRepository:
    def __init__(self, connection):
        self._conn = connection

    def list_all(self) -> list[Task]:
        rows = self._conn.execute(
            """
            SELECT * FROM task
            ORDER BY
                status ASC,
                priority DESC,
                sort_order ASC,
                created_at DESC
            """
        ).fetchall()
        return [_row_to_task(row) for row in rows]

    def get(self, task_id: int) -> Optional[Task]:
        row = self._conn.execute("SELECT * FROM task WHERE id = ?", (task_id,)).fetchone()
        return _row_to_task(row) if row else None

    def add(self, task: Task) -> Task:
        now = datetime.now()
        cursor = self._conn.execute(
            """
            INSERT INTO task (
                title, description, status, priority, due_time,
                reminder_minutes, reminded_at, completed_at,
                sort_order, created_at, updated_at, category, include_in_report
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.title.strip(),
                task.description.strip(),
                task.status,
                task.priority,
                dump_dt(task.due_time),
                task.reminder_minutes,
                dump_dt(task.reminded_at),
                dump_dt(task.completed_at),
                task.sort_order,
                dump_dt(task.created_at or now),
                dump_dt(now),
                task.category or "工作",
                1 if task.include_in_report else 0,
            ),
        )
        self._conn.commit()
        created = self.get(cursor.lastrowid)
        assert created is not None
        return created

    def update(self, task: Task) -> Task:
        if task.id is None:
            raise ValueError("Cannot update a task without id")
        now = datetime.now()
        self._conn.execute(
            """
            UPDATE task SET
                title = ?, description = ?, status = ?, priority = ?,
                due_time = ?, reminder_minutes = ?, reminded_at = ?,
                completed_at = ?, sort_order = ?, updated_at = ?,
                category = ?, include_in_report = ?
            WHERE id = ?
            """,
            (
                task.title.strip(),
                task.description.strip(),
                task.status,
                task.priority,
                dump_dt(task.due_time),
                task.reminder_minutes,
                dump_dt(task.reminded_at),
                dump_dt(task.completed_at),
                task.sort_order,
                dump_dt(now),
                task.category or "工作",
                1 if task.include_in_report else 0,
                task.id,
            ),
        )
        self._conn.commit()
        updated = self.get(task.id)
        assert updated is not None
        return updated

    def delete(self, task_id: int) -> None:
        self._conn.execute("DELETE FROM task WHERE id = ?", (task_id,))
        self._conn.commit()

    def min_sort_order(self) -> int:
        row = self._conn.execute(
            "SELECT MIN(sort_order) AS value FROM task WHERE status = ?",
            (TaskStatus.PENDING,),
        ).fetchone()
        value = row["value"] if row else None
        return 0 if value is None else int(value)
