from __future__ import annotations

from datetime import datetime
from typing import Optional

from database.common import dump_dt, parse_dt, row_value
from model.memo import Memo


def _row_to_memo(row) -> Memo:
    return Memo(
        id=row["id"],
        title=row["title"] or "",
        content=row["content"] or "",
        category=row["category"] or "工作",
        tags=row["tags"] or "",
        is_pinned=bool(row["is_pinned"]),
        include_in_report=bool(row["include_in_report"]),
        task_id=row_value(row, "task_id"),
        created_at=parse_dt(row["created_at"]),
        updated_at=parse_dt(row["updated_at"]),
    )


class MemoRepository:
    def __init__(self, connection):
        self._conn = connection

    def list_all(self) -> list[Memo]:
        rows = self._conn.execute(
            """
            SELECT * FROM memo
            ORDER BY is_pinned DESC, updated_at DESC
            """
        ).fetchall()
        return [_row_to_memo(row) for row in rows]

    def get(self, memo_id: int) -> Optional[Memo]:
        row = self._conn.execute("SELECT * FROM memo WHERE id = ?", (memo_id,)).fetchone()
        return _row_to_memo(row) if row else None

    def add(self, memo: Memo) -> Memo:
        now = datetime.now()
        cursor = self._conn.execute(
            """
            INSERT INTO memo (
                title, content, category, tags, is_pinned,
                include_in_report, task_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memo.title.strip(),
                memo.content.strip(),
                memo.category or "工作",
                memo.tags.strip(),
                1 if memo.is_pinned else 0,
                1 if memo.include_in_report else 0,
                memo.task_id,
                dump_dt(memo.created_at or now),
                dump_dt(now),
            ),
        )
        self._conn.commit()
        created = self.get(cursor.lastrowid)
        assert created is not None
        return created

    def update(self, memo: Memo) -> Memo:
        if memo.id is None:
            raise ValueError("Cannot update a memo without id")
        now = datetime.now()
        self._conn.execute(
            """
            UPDATE memo SET
                title = ?, content = ?, category = ?, tags = ?,
                is_pinned = ?, include_in_report = ?, task_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                memo.title.strip(),
                memo.content.strip(),
                memo.category or "工作",
                memo.tags.strip(),
                1 if memo.is_pinned else 0,
                1 if memo.include_in_report else 0,
                memo.task_id,
                dump_dt(now),
                memo.id,
            ),
        )
        self._conn.commit()
        updated = self.get(memo.id)
        assert updated is not None
        return updated

    def delete(self, memo_id: int) -> None:
        self._conn.execute("DELETE FROM memo WHERE id = ?", (memo_id,))
        self._conn.commit()
