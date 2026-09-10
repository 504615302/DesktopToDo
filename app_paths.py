"""Application path helpers. Works in source and PyInstaller-frozen builds."""

from __future__ import annotations

import sys
from pathlib import Path


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def data_dir() -> Path:
    path = app_dir() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    path = app_dir() / "config"
    path.mkdir(parents=True, exist_ok=True)
    return path


def resources_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", app_dir())) / "resources"
    return app_dir() / "resources"


def db_path() -> Path:
    return data_dir() / "todo.db"


def settings_path() -> Path:
    return config_dir() / "settings.json"


def icon_path(*parts: str) -> Path:
    return resources_dir() / "icons" / Path(*parts)
