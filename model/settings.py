from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Optional

VALID_THEMES = {"cute", "business", "minimal"}
_LEGACY_THEME = {"light": "minimal", "dark": "business", "system": "minimal"}


@dataclass
class AppSettings:
    always_on_top: bool = False
    lock_position: bool = False
    auto_start: bool = False
    opacity: float = 0.95
    theme: str = "minimal"
    window_x: Optional[int] = None
    window_y: Optional[int] = None
    window_width: int = 400
    window_height: int = 640
    filter_mode: str = "today"
    current_page: str = "today"
    default_ai_model: int | None = None
    default_report_template: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppSettings":
        allowed = {item.name for item in fields(cls)}
        cleaned = {key: value for key, value in data.items() if key in allowed}
        settings = cls(**cleaned)
        settings.opacity = min(1.0, max(0.0, float(settings.opacity)))
        settings.theme = _LEGACY_THEME.get(settings.theme, settings.theme)
        if settings.theme not in VALID_THEMES:
            settings.theme = "minimal"
        settings.always_on_top = bool(settings.always_on_top)
        settings.window_width = max(360, int(settings.window_width))
        settings.window_height = max(400, int(settings.window_height))
        return settings

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
