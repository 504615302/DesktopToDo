from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Optional


@dataclass
class AppSettings:
    always_on_top: bool = True
    auto_start: bool = False
    opacity: float = 0.9
    theme: str = "system"
    window_x: Optional[int] = None
    window_y: Optional[int] = None
    window_width: int = 360
    window_height: int = 600
    filter_mode: str = "incomplete"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppSettings":
        allowed = {item.name for item in fields(cls)}
        cleaned = {key: value for key, value in data.items() if key in allowed}
        settings = cls(**cleaned)
        settings.opacity = min(1.0, max(0.7, float(settings.opacity)))
        if settings.theme not in {"light", "dark", "system"}:
            settings.theme = "system"
        settings.window_width = max(300, int(settings.window_width))
        settings.window_height = max(400, int(settings.window_height))
        return settings

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
