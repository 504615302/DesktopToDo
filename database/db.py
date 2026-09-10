from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 1,
    due_time DATETIME,
    reminder_minutes INTEGER,
    reminded_at DATETIME,
    completed_at DATETIME,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME,
    category TEXT DEFAULT '工作',
    include_in_report INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS memo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT NOT NULL,
    category TEXT,
    tags TEXT,
    is_pinned INTEGER DEFAULT 0,
    include_in_report INTEGER DEFAULT 1,
    task_id INTEGER,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS report_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    is_default INTEGER DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS ai_model_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    provider TEXT,
    api_base TEXT,
    model_name TEXT,
    encrypted_api_key TEXT,
    temperature REAL DEFAULT 0.3,
    max_tokens INTEGER DEFAULT 4000,
    enabled INTEGER DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS weekly_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    start_date DATE,
    end_date DATE,
    template_id INTEGER,
    model_config_id INTEGER,
    content TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_task_status ON task(status);
CREATE INDEX IF NOT EXISTS idx_task_sort ON task(sort_order);
CREATE INDEX IF NOT EXISTS idx_memo_updated ON memo(updated_at);
"""

_TASK_COLUMNS = {
    "reminder_minutes": "INTEGER",
    "reminded_at": "DATETIME",
    "category": "TEXT DEFAULT '工作'",
    "include_in_report": "INTEGER DEFAULT 1",
}

DEFAULT_TEMPLATE = """周报时间：{{start_date}} - {{end_date}}

一、本周工作

{{completed_tasks}}

二、工作记录

{{memos}}

三、下周计划

{{unfinished_tasks}}

四、当前问题

无

五、待协调事项

无
"""

DEFAULT_TEMPLATES = [
    ("公司标准模板", DEFAULT_TEMPLATE, 1),
    (
        "简洁模板",
        "本周完成\n{{completed_tasks}}\n\n下周计划\n{{unfinished_tasks}}\n\n备注\n{{memos}}{{user_notes}}",
        0,
    ),
    (
        "技术研发模板",
        "周期：{{start_date}} ~ {{end_date}}\n\n一、研发进展\n{{completed_tasks}}\n\n二、技术记录\n{{memos}}\n\n三、待办与风险\n{{unfinished_tasks}}\n{{user_notes}}",
        0,
    ),
]


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(self.path))
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self.initialize()

    def initialize(self) -> None:
        self._connection.executescript(SCHEMA)
        existing = {row["name"] for row in self._connection.execute("PRAGMA table_info(task)")}
        for name, definition in _TASK_COLUMNS.items():
            if name not in existing:
                self._connection.execute(f"ALTER TABLE task ADD COLUMN {name} {definition}")
        self._migrate_priority()
        self._seed_templates()
        self._connection.commit()

    def _meta(self, key: str) -> str | None:
        row = self._connection.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return None if row is None else row["value"]

    def _set_meta(self, key: str, value: str) -> None:
        self._connection.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )

    def _migrate_priority(self) -> None:
        if self._meta("priority_v2") == "1":
            return
        self._connection.execute(
            """
            UPDATE task SET priority = CASE priority
                WHEN 0 THEN 1
                WHEN 1 THEN 2
                WHEN 2 THEN 3
                ELSE priority
            END
            """
        )
        self._set_meta("priority_v2", "1")

    def _seed_templates(self) -> None:
        count = self._connection.execute("SELECT COUNT(*) AS n FROM report_template").fetchone()["n"]
        if count:
            return
        now = datetime.now().isoformat(timespec="seconds")
        for name, content, is_default in DEFAULT_TEMPLATES:
            self._connection.execute(
                """
                INSERT INTO report_template (name, content, is_default, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, content, is_default, now, now),
            )

    def connection(self) -> sqlite3.Connection:
        return self._connection

    def close(self) -> None:
        self._connection.close()
