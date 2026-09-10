from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class ReportTemplate:
    name: str
    content: str
    id: Optional[int] = None
    is_default: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class WeeklyReport:
    content: str
    id: Optional[int] = None
    title: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    template_id: Optional[int] = None
    model_config_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class AIModelConfig:
    name: str
    id: Optional[int] = None
    provider: str = "openai-compatible"
    api_base: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o-mini"
    encrypted_api_key: str = ""
    temperature: float = 0.3
    max_tokens: int = 4000
    enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def masked_key(self) -> str:
        if not self.encrypted_api_key:
            return "未配置"
        return "sk-****************"
