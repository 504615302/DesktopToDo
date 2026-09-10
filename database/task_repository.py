from __future__ import annotations

from datetime import datetime
from typing import Optional

from model.task import Task, TaskStatus


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _dump_dt(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat(timespec="seconds")


def _row_to_task(row) -> Task:
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"] or "",
        status=row["status"] or 0,
        priority=row["priority"] or 0,
        due_time=_parse_dt(row["due_time"]),
        completed_at=_parse_dt(row["completed_at"]),
        sort_order=row["sort_order"] or 0,
        created_at=_parse_dt(row["created_at"]),
        updated_at=_parse_dt(row["updated_at"]),
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
                completed_at, sort_order, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.title.strip(),
                task.description.strip(),
                task.status,
                task.priority,
                _dump_dt(task.due_time),
                _dump_dt(task.completed_at),
                task.sort_order,
                _dump_dt(task.created_at or now),
                _dump_dt(now),
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
                due_time = ?, completed_at = ?, sort_order = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                task.title.strip(),
                task.description.strip(),
                task.status,
                task.priority,
                _dump_dt(task.due_time),
                _dump_dt(task.completed_at),
                task.sort_order,
                _dump_dt(now),
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
