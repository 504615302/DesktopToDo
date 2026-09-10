from dataclasses import dataclass

from service.ai_service import AIService
from service.credential_service import CredentialService
from service.memo_service import MemoService
from service.reminder_service import ReminderService
from service.report_service import ReportService
from service.settings_service import SettingsService
from service.startup_service import StartupService
from service.task_service import TaskService


@dataclass
class AppContext:
    tasks: TaskService
    memos: MemoService
    reports: ReportService
    ai: AIService
    credentials: CredentialService
    settings: SettingsService
    startup: StartupService
    reminders: ReminderService | None = None
