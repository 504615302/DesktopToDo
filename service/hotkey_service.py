from __future__ import annotations

import ctypes
from ctypes import wintypes
import sys

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Signal

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
WM_HOTKEY = 0x0312
HOTKEYS = {
    1: "todo",
    2: "memo",
    3: "report",
}


class _HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, owner: "HotkeyService"):
        super().__init__()
        self._owner = owner

    def nativeEventFilter(self, event_type, message):  # noqa: N802
        if sys.platform != "win32":
            return False, 0
        kind = bytes(event_type).decode("ascii", "ignore") if not isinstance(event_type, str) else event_type
        if "windows_generic_MSG" not in kind:
            return False, 0
        try:
            msg = wintypes.MSG.from_address(int(message))
        except (TypeError, ValueError, AttributeError):
            return False, 0
        if msg.message == WM_HOTKEY:
            action = HOTKEYS.get(int(msg.wParam))
            if action:
                self._owner.activated.emit(action)
                return True, 0
        return False, 0


class HotkeyService(QObject):
    activated = Signal(str)

    def __init__(self, hwnd: int, parent=None):
        super().__init__(parent)
        self._hwnd = hwnd
        self._filter = _HotkeyFilter(self)
        self._registered = False

    def install(self, app) -> None:
        if sys.platform != "win32":
            return
        user32 = ctypes.windll.user32
        vk = {"todo": 0x54, "memo": 0x4E, "report": 0x57}
        registered_any = False
        for hot_id, name in HOTKEYS.items():
            if user32.RegisterHotKey(self._hwnd, hot_id, MOD_CONTROL | MOD_ALT, vk[name]):
                registered_any = True
        if registered_any:
            app.installNativeEventFilter(self._filter)
        self._registered = True

    def uninstall(self) -> None:
        if not self._registered:
            return
        user32 = ctypes.windll.user32
        for hot_id in HOTKEYS:
            user32.UnregisterHotKey(self._hwnd, hot_id)
        self._registered = False
