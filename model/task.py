from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import IntEnum
from typing import Optional


class TaskStatus(IntEnum):
    PENDING = 0
    COMPLETED = 1


class Priority(IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3

    @property
    def label(self) -> str:
        return {self.LOW: "低", self.NORMAL: "普通", self.HIGH: "高", self.URGENT: "紧急"}[self]


CATEGORIES = ["工作", "生活", "学习", "其他"]


@dataclass
class Task:
    title: str
    id: Optional[int] = None
    description: str = ""
    status: int = TaskStatus.PENDING
    priority: int = Priority.NORMAL
    due_time: Optional[datetime] = None
    reminder_minutes: Optional[int] = None
    reminded_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    sort_order: int = 0
    created_at: Optional[datetime] = field(default=None)
    updated_at: Optional[datetime] = field(default=None)
    category: str = "工作"
    include_in_report: bool = True

    @property
    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    @property
    def priority_enum(self) -> Priority:
        try:
            return Priority(self.priority)
        except ValueError:
            return Priority.NORMAL

    @property
    def is_overdue(self) -> bool:
        return bool(self.due_time and not self.is_completed and self.due_time < datetime.now())

    def reminder_at(self) -> Optional[datetime]:
        if self.due_time is None or self.reminder_minutes is None:
            return None
        return self.due_time - timedelta(minutes=self.reminder_minutes)

    def due_label(self) -> str:
        if self.due_time is None:
            return ""
        if self.is_overdue:
            return "已逾期"
        now = datetime.now()
        due_date = self.due_time.date()
        time_part = self.due_time.strftime("%H:%M")
        if due_date == now.date():
            prefix = "今天"
        elif due_date == (now + timedelta(days=1)).date():
            prefix = "明天"
        else:
            prefix = self.due_time.strftime("%m-%d")
        if time_part == "00:00":
            return prefix
        return f"{prefix} {time_part}"

    def reminder_message(self) -> str:
        if self.reminder_minutes == 0:
            return f"{self.title} 到时间了"
        if self.reminder_minutes:
            return f"{self.title} 将在 {self.reminder_minutes} 分钟后到期"
        return f"{self.title} 需要处理"

    def is_today(self) -> bool:
        today = datetime.now().date()
        if self.due_time and self.due_time.date() == today:
            return True
        if self.created_at and self.created_at.date() == today and self.due_time is None:
            return True
        if self.completed_at and self.completed_at.date() == today:
            return True
        return False
