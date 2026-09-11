from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datetime import datetime, timedelta

from database.db import Database
from database.memo_repository import MemoRepository
from database.report_repository import ReportRepository
from database.task_repository import TaskRepository
from model.task import Priority, TaskStatus
from service.ai_service import AIService
from service.credential_service import CredentialService
from service.memo_service import MemoService
from service.report_service import ReportService, week_range
from service.settings_service import SettingsService
from service.task_service import TaskService


def test_user_data_root_in_dev() -> None:
    from app_paths import exe_dir, is_portable, user_data_root

    assert is_portable() is True
    assert user_data_root() == exe_dir()


def test_task_and_settings_roundtrip() -> None:
    tmp_dir = TemporaryDirectory(ignore_cleanup_errors=True)
    tmp = Path(tmp_dir.name)
    db = Database(tmp / "todo.db")
    try:
        service = TaskService(TaskRepository(db.connection()))
        first = service.add_task("task-a")
        assert first.id is not None
        assert first.priority == Priority.NORMAL
        assert first.include_in_report is True
        life = service.add_task("洗车", category="生活")
        assert life.include_in_report is False
        service.set_completed(first, True)
        loaded = next(item for item in service.list_tasks() if item.id == first.id)
        assert loaded.status == TaskStatus.COMPLETED
        assert loaded.completed_at is not None
        service.set_completed(loaded, False)
        pending = next(item for item in service.list_tasks() if item.id == first.id)
        pending.description = "details"
        pending.priority = 2
        service.update_task(pending)
        second = service.add_task("task-b")
        titles = [item.title for item in service.list_tasks() if item.category != "生活"]
        assert titles[0] == "task-a"
        assert "task-b" in titles
        service.delete_task(first.id)
        titles = [item.title for item in service.list_tasks()]
        assert "task-a" not in titles
        assert second.description == ""

        settings = SettingsService(tmp / "settings.json")
        settings.update(always_on_top=False, opacity=0.0, theme="cute", lock_position=True, hotkey_todo="Ctrl+Shift+T")
        again = SettingsService(tmp / "settings.json")
        assert again.settings.always_on_top is False
        assert again.settings.opacity == 0.0
        assert again.settings.theme == "cute"
        assert again.settings.lock_position is True
        assert again.settings.hotkey_todo == "Ctrl+Shift+T"

        due = datetime.now() + timedelta(minutes=5)
        reminder_task = service.add_task("remind-me")
        reminder_task.due_time = due
        reminder_task.reminder_minutes = 10
        service.update_task(reminder_task)
        ready = service.due_reminders(datetime.now())
        assert ready and ready[0].title == "remind-me"
        service.mark_reminded(ready[0])
        assert service.due_reminders(datetime.now()) == []

        memos = MemoService(MemoRepository(db.connection()))
        note = memos.add_memo("MCP字段需要统一snake_case", tags="#工作")
        assert note.id is not None
        found = memos.search("MCP")
        assert found and found[0].id == note.id

        credentials = CredentialService()
        reports = ReportService(ReportRepository(db.connection()), AIService(credentials), credentials)
        templates = reports.templates()
        assert templates
        assert any(item.is_default for item in templates)
        start, end = week_range("this")
        materials = reports.collect_materials(service.list_tasks(), memos.list_memos(), start, end)
        assert "completed" in materials
        secret = credentials.encrypt("sk-test")
        assert credentials.decrypt(secret) == "sk-test"

        from model.report import AIModelConfig
        from service.ai_service import build_chat_payload, prefers_completion_tokens

        assert prefers_completion_tokens("gpt-5")
        assert prefers_completion_tokens("gpt-5-mini")
        assert not prefers_completion_tokens("deepseek-chat")
        payload = build_chat_payload(
            AIModelConfig(name="gpt5", model_name="gpt-5"),
            "ok",
            32,
            use_completion_tokens=True,
            include_temperature=True,
        )
        assert "max_completion_tokens" in payload
        assert "max_tokens" not in payload
        from service.ai_service import QA_SYSTEM_PROMPT
        from service.chat_service import build_qa_context

        qa = build_chat_payload(
            AIModelConfig(name="qa", model_name="gpt-4o-mini"),
            "",
            32,
            use_completion_tokens=False,
            include_temperature=True,
            system_prompt=QA_SYSTEM_PROMPT,
            history=[{"role": "user", "content": "今天做什么"}],
        )
        assert qa["messages"][0]["content"] == QA_SYSTEM_PROMPT
        assert qa["messages"][-1]["content"] == "今天做什么"
        context = build_qa_context([first], [note], include_tasks=True, include_memos=True)
        assert "未完成待办" in context or "最近已完成" in context
        assert "MCP" in context
        from datetime import date as date_cls

        from service.tools_service import (
            ToolsError,
            almanac_for,
            day_ganzhi,
            decode_base64,
            encode_base64,
            format_json,
            minify_json,
            naming_styles,
            parse_name_words,
            parse_time_value,
            split_identifier,
            time_snapshot,
        )

        pretty = format_json('{"a":1}')
        assert '"a"' in pretty and "1" in pretty
        assert minify_json(pretty) == '{"a":1}'
        assert decode_base64(encode_base64("桌面")) == "桌面"
        stamp = parse_time_value("2026-09-11 10:32:00")
        snap = time_snapshot(stamp)
        assert snap["local"] == "2026-09-11 10:32:00"
        assert parse_time_value(snap["seconds"]).year == 2026
        assert split_identifier("userName") == ["user", "name"]
        assert split_identifier("HTTPServer") == ["http", "server"]
        styles = naming_styles(["user", "name"])
        assert styles["snake_case"] == "user_name"
        assert styles["camelCase"] == "userName"
        assert styles["PascalCase"] == "UserName"
        assert styles["CONSTANT"] == "USER_NAME"
        assert styles["kebab-case"] == "user-name"
        assert parse_name_words("get user profile!") == ["get", "user", "profile"]
        try:
            split_identifier("用户名")
            raise AssertionError("chinese should require AI")
        except ToolsError:
            pass
        gan, zhi = day_ganzhi(date_cls(1899, 12, 22))
        assert gan == "甲" and zhi == "子"
        almanac = almanac_for(date_cls(2026, 9, 11))
        assert almanac == almanac_for(date_cls(2026, 9, 11))
        assert "2026年09月11日" in almanac
        assert "宜" in almanac and "忌" in almanac
    finally:
        db.close()
        tmp_dir.cleanup()


if __name__ == "__main__":
    test_user_data_root_in_dev()
    test_task_and_settings_roundtrip()
    print("service ok")
