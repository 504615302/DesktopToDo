from __future__ import annotations

from datetime import date, datetime, timedelta

from database.report_repository import ReportRepository
from model.memo import Memo
from model.report import AIModelConfig, ReportTemplate, WeeklyReport
from model.task import Task
from service.ai_service import AIService
from service.credential_service import CredentialService


def week_range(kind: str = "this") -> tuple[date, date]:
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=4)
    if kind == "last":
        start -= timedelta(days=7)
        end -= timedelta(days=7)
    return start, end


def week_title(start: date, end: date) -> str:
    iso = start.isocalendar()
    return f"{iso[0]}年第{iso[1]}周 {start.strftime('%m-%d')} ~ {end.strftime('%m-%d')}"


def _in_range(value: datetime | None, start: date, end: date) -> bool:
    if value is None:
        return False
    return start <= value.date() <= end


class ReportService:
    def __init__(self, repository: ReportRepository, ai: AIService, credentials: CredentialService):
        self._repo = repository
        self.ai = ai
        self.credentials = credentials

    def templates(self) -> list[ReportTemplate]:
        return self._repo.list_templates()

    def save_template(self, template: ReportTemplate) -> ReportTemplate:
        return self._repo.save_template(template)

    def delete_template(self, template_id: int) -> None:
        self._repo.delete_template(template_id)

    def models(self) -> list[AIModelConfig]:
        return self._repo.list_models()

    def save_model(self, config: AIModelConfig, raw_key: str | None = None) -> AIModelConfig:
        if raw_key:
            config.encrypted_api_key = self.credentials.encrypt(raw_key)
        return self._repo.save_model(config)

    def delete_model(self, model_id: int) -> None:
        self._repo.delete_model(model_id)

    def reports(self) -> list[WeeklyReport]:
        return self._repo.list_reports()

    def save_report(self, report: WeeklyReport) -> WeeklyReport:
        return self._repo.save_report(report)

    def delete_report(self, report_id: int) -> None:
        self._repo.delete_report(report_id)

    def collect_materials(
        self,
        tasks: list[Task],
        memos: list[Memo],
        start: date,
        end: date,
    ) -> dict[str, list]:
        completed = [
            task
            for task in tasks
            if task.is_completed
            and task.include_in_report
            and (_in_range(task.completed_at, start, end) or _in_range(task.updated_at, start, end))
        ]
        unfinished = [
            task
            for task in tasks
            if not task.is_completed and task.include_in_report
        ]
        notes = [
            memo
            for memo in memos
            if memo.include_in_report and (_in_range(memo.updated_at, start, end) or _in_range(memo.created_at, start, end))
        ]
        return {"completed": completed, "unfinished": unfinished, "memos": notes}

    def build_prompt(
        self,
        template: ReportTemplate,
        start: date,
        end: date,
        completed: list[Task],
        unfinished: list[Task],
        memos: list[Memo],
        user_notes: str,
    ) -> str:
        completed_text = "\n".join(f"- {task.title}" + (f"：{task.description}" if task.description else "") for task in completed) or "无"
        unfinished_text = "\n".join(f"- {task.title}" for task in unfinished) or "无"
        memo_text = "\n".join(f"- {memo.display_title()}：{memo.content}" for memo in memos) or "无"
        notes = user_notes.strip() or "无"
        filled = (
            template.content.replace("{{start_date}}", start.isoformat())
            .replace("{{end_date}}", end.isoformat())
            .replace("{{completed_tasks}}", completed_text)
            .replace("{{unfinished_tasks}}", unfinished_text)
            .replace("{{memos}}", memo_text)
            .replace("{{user_notes}}", notes)
        )
        return (
            f"时间范围：{start.isoformat()} ~ {end.isoformat()}\n\n"
            f"已完成任务：\n{completed_text}\n\n"
            f"未完成任务：\n{unfinished_text}\n\n"
            f"备忘录：\n{memo_text}\n\n"
            f"用户补充：\n{notes}\n\n"
            f"请严格按以下模板输出周报：\n{filled}"
        )
