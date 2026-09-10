from __future__ import annotations

import json
from pathlib import Path

from model.settings import AppSettings


class SettingsService:
    def __init__(self, path: Path):
        self.path = path
        self.settings = self.load()

    def load(self) -> AppSettings:
        if not self.path.exists():
            settings = AppSettings()
            self.save(settings)
            return settings
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return AppSettings()
            return AppSettings.from_dict(data)
        except (OSError, json.JSONDecodeError):
            return AppSettings()

    def save(self, settings: AppSettings | None = None) -> None:
        if settings is not None:
            self.settings = settings
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.settings.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def update(self, **kwargs) -> AppSettings:
        current = self.settings.to_dict()
        current.update(kwargs)
        self.settings = AppSettings.from_dict(current)
        self.save()
        return self.settings
