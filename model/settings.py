from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Optional

VALID_THEMES = {"cute", "business", "minimal", "tech"}
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
    compact_mode: bool = False
    default_ai_model: int | None = None
    default_report_template: int | None = None
    qa_temperature: float | None = None
    qa_max_tokens: int | None = None
    hotkey_todo: str = "Ctrl+Alt+T"
    hotkey_memo: str = "Ctrl+Alt+N"
    hotkey_report: str = "Ctrl+Alt+W"
    hotkey_chat: str = "Ctrl+Alt+Q"
    hotkey_hide: str = "Ctrl+Alt+H"

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
        settings.compact_mode = bool(settings.compact_mode)
        settings.window_width = max(360, int(settings.window_width))
        settings.window_height = max(400, int(settings.window_height))
        if settings.qa_temperature is not None:
            settings.qa_temperature = min(2.0, max(0.0, float(settings.qa_temperature)))
        if settings.qa_max_tokens is not None:
            settings.qa_max_tokens = min(8192, max(256, int(settings.qa_max_tokens)))
        settings.hotkey_todo = str(settings.hotkey_todo or "Ctrl+Alt+T")
        settings.hotkey_memo = str(settings.hotkey_memo or "Ctrl+Alt+N")
        settings.hotkey_report = str(settings.hotkey_report or "Ctrl+Alt+W")
        settings.hotkey_chat = str(settings.hotkey_chat or "Ctrl+Alt+Q")
        settings.hotkey_hide = str(settings.hotkey_hide or "Ctrl+Alt+H")
        return settings

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
