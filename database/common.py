from __future__ import annotations

from datetime import datetime
from typing import Optional


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)


def dump_dt(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat(timespec="seconds")


def row_value(row, key: str, default=None):
    try:
        value = row[key]
    except (KeyError, IndexError):
        return default
    return default if value is None else value
