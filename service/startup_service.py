from __future__ import annotations

import sys
from pathlib import Path

APP_RUN_NAME = "DesktopTODO"


def _startup_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{Path(sys.executable).resolve()}"'
    python = Path(sys.executable)
    if python.name.lower() == "python.exe":
        pythonw = python.with_name("pythonw.exe")
        if pythonw.exists():
            python = pythonw
    script = Path(__file__).resolve().parents[1] / "main.py"
    return f'"{python}" "{script}"'


class StartupService:
    def is_enabled(self) -> bool:
        try:
            import winreg
        except ImportError:
            return False
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ,
            ) as key:
                value, _ = winreg.QueryValueEx(key, APP_RUN_NAME)
                return bool(value)
        except OSError:
            return False

    def set_enabled(self, enabled: bool) -> None:
        try:
            import winreg
        except ImportError:
            return
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            if enabled:
                winreg.SetValueEx(key, APP_RUN_NAME, 0, winreg.REG_SZ, _startup_command())
            else:
                try:
                    winreg.DeleteValue(key, APP_RUN_NAME)
                except FileNotFoundError:
                    pass
