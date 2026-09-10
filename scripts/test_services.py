from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.db import Database
from database.task_repository import TaskRepository
from model.task import TaskStatus
from service.settings_service import SettingsService
from service.task_service import TaskService


def test_task_and_settings_roundtrip() -> None:
    tmp_dir = TemporaryDirectory(ignore_cleanup_errors=True)
    tmp = Path(tmp_dir.name)
    db = Database(tmp / "todo.db")
    try:
        service = TaskService(TaskRepository(db.connection()))
        first = service.add_task("task-a")
        assert first.id is not None
        service.set_completed(first, True)
        loaded = service.list_tasks()[0]
        assert loaded.status == TaskStatus.COMPLETED
        assert loaded.completed_at is not None
        service.set_completed(loaded, False)
        pending = service.list_tasks()[0]
        pending.description = "details"
        pending.priority = 2
        service.update_task(pending)
        second = service.add_task("task-b")
        titles = [item.title for item in service.list_tasks()]
        assert titles[0] == "task-a"
        assert titles[1] == "task-b"
        service.delete_task(first.id)
        titles = [item.title for item in service.list_tasks()]
        assert titles == ["task-b"]
        assert second.description == ""

        settings = SettingsService(tmp / "settings.json")
        settings.update(always_on_top=False, opacity=0.8)
        again = SettingsService(tmp / "settings.json")
        assert again.settings.always_on_top is False
        assert again.settings.opacity == 0.8
    finally:
        db.close()
        tmp_dir.cleanup()


if __name__ == "__main__":
    test_task_and_settings_roundtrip()
    print("service ok")
