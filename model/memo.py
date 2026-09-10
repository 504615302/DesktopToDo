from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Memo:
    content: str
    id: Optional[int] = None
    title: str = ""
    category: str = "工作"
    tags: str = ""
    is_pinned: bool = False
    include_in_report: bool = True
    task_id: Optional[int] = None
    created_at: Optional[datetime] = field(default=None)
    updated_at: Optional[datetime] = field(default=None)

    def display_title(self) -> str:
        if self.title.strip():
            return self.title.strip()
        line = self.content.strip().splitlines()[0] if self.content.strip() else "未命名备忘"
        return line[:40]
