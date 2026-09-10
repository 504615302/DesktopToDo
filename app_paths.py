"""Application path helpers. Works in source, portable EXE, and installed builds."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_FOLDER = "DesktopToDo"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def exe_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def app_dir() -> Path:
    return exe_dir()


def _under_env_dir(path: Path, env_key: str) -> bool:
    base = os.environ.get(env_key)
    if not base:
        return False
    try:
        path.resolve().relative_to(Path(base).resolve())
        return True
    except ValueError:
        return False


def _is_installed_layout(path: Path) -> bool:
    if any(_under_env_dir(path, key) for key in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432")):
        return True
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return False
    installed = Path(local) / "Programs" / APP_FOLDER
    try:
        path.resolve().relative_to(installed.resolve())
        return True
    except ValueError:
        return False


def _can_write(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".desktop-todo-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def is_portable() -> bool:
    root = exe_dir()
    if (root / "portable.txt").exists() or (root / "portable").exists():
        return True
    if not is_frozen():
        return True
    if _is_installed_layout(root):
        return False
    return _can_write(root)


def user_data_root() -> Path:
    if is_portable():
        return exe_dir()
    local = os.environ.get("LOCALAPPDATA")
    root = Path(local) / APP_FOLDER if local else Path.home() / "AppData" / "Local" / APP_FOLDER
    root.mkdir(parents=True, exist_ok=True)
    return root


def data_dir() -> Path:
    path = user_data_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    path = user_data_root() / "config"
    path.mkdir(parents=True, exist_ok=True)
    return path


def resources_dir() -> Path:
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", exe_dir())) / "resources"
    return exe_dir() / "resources"


def db_path() -> Path:
    return data_dir() / "todo.db"


def settings_path() -> Path:
    return config_dir() / "settings.json"


def icon_path(*parts: str) -> Path:
    return resources_dir() / "icons" / Path(*parts)


def pay_path(name: str) -> Path:
    return resources_dir() / "pay" / name
