from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Optional


class TaskStatus(IntEnum):
    PENDING = 0
    COMPLETED = 1


class Priority(IntEnum):
    NORMAL = 0
    IMPORTANT = 1
    URGENT = 2

    @property
    def label(self) -> str:
        return {self.NORMAL: "普通", self.IMPORTANT: "重要", self.URGENT: "紧急"}[self]

    @property
    def icon(self) -> str:
        return {self.NORMAL: "", self.IMPORTANT: "★", self.URGENT: "🔥"}[self]


@dataclass
class Task:
    title: str
    id: Optional[int] = None
    description: str = ""
    status: int = TaskStatus.PENDING
    priority: int = Priority.NORMAL
    due_time: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    sort_order: int = 0
    created_at: Optional[datetime] = field(default=None)
    updated_at: Optional[datetime] = field(default=None)

    @property
    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    @property
    def priority_enum(self) -> Priority:
        try:
            return Priority(self.priority)
        except ValueError:
            return Priority.NORMAL
