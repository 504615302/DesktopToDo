from __future__ import annotations

import ctypes
from ctypes import wintypes
import sys

from PySide6.QtCore import QAbstractNativeEventFilter, QKeyCombination, QObject, Qt, Signal
from PySide6.QtGui import QKeySequence

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

DEFAULT_HOTKEYS = {
    "todo": "Ctrl+Alt+T",
    "memo": "Ctrl+Alt+N",
    "report": "Ctrl+Alt+W",
    "chat": "Ctrl+Alt+Q",
    "hide": "Ctrl+Alt+H",
}

HOTKEY_IDS = {
    "todo": 1,
    "memo": 2,
    "report": 3,
    "chat": 4,
    "hide": 5,
}

_VK_EXTRA = {
    int(Qt.Key_Space): 0x20,
    int(Qt.Key_Tab): 0x09,
    int(Qt.Key_Insert): 0x2D,
    int(Qt.Key_Delete): 0x2E,
    int(Qt.Key_Home): 0x24,
    int(Qt.Key_End): 0x23,
    int(Qt.Key_PageUp): 0x21,
    int(Qt.Key_PageDown): 0x22,
    int(Qt.Key_Left): 0x25,
    int(Qt.Key_Up): 0x26,
    int(Qt.Key_Right): 0x27,
    int(Qt.Key_Down): 0x28,
    int(Qt.Key_Plus): 0xBB,
    int(Qt.Key_Minus): 0xBD,
    int(Qt.Key_Comma): 0xBC,
    int(Qt.Key_Period): 0xBE,
    int(Qt.Key_Slash): 0xBF,
    int(Qt.Key_Semicolon): 0xBA,
    int(Qt.Key_BracketLeft): 0xDB,
    int(Qt.Key_BracketRight): 0xDD,
    int(Qt.Key_Backslash): 0xDC,
    int(Qt.Key_QuoteLeft): 0xC0,
    int(Qt.Key_Apostrophe): 0xDE,
}

_CTRL_LETTER_KEYS = {
    int(Qt.Key_Backspace): Qt.Key_H,
    int(Qt.Key_Tab): Qt.Key_I,
    int(Qt.Key_Return): Qt.Key_M,
    int(Qt.Key_Enter): Qt.Key_M,
}


def restore_ctrl_letter_key(key: int, modifiers, native_vk: int = 0) -> int:
    if native_vk and 0x41 <= native_vk <= 0x5A:
        return native_vk
    if native_vk and 0x30 <= native_vk <= 0x39:
        return native_vk
    if modifiers & Qt.KeyboardModifier.ControlModifier:
        mapped = _CTRL_LETTER_KEYS.get(int(key))
        if mapped is not None:
            return int(mapped)
    return int(key)


def normalize_hotkey(text: str, fallback: str = "") -> str:
    sequence = QKeySequence((text or "").strip())
    if sequence.count() < 1:
        return fallback
    portable = sequence.toString(QKeySequence.PortableText)
    if parse_hotkey(portable) is None:
        return fallback
    return portable


def parse_hotkey(text: str) -> tuple[int, int] | None:
    sequence = QKeySequence((text or "").strip())
    if sequence.count() < 1:
        return None
    item = sequence[0]
    if isinstance(item, QKeyCombination):
        key = int(item.key())
        mods = item.keyboardModifiers()
    else:
        key = int(item) & 0x01FFFFFF
        mods = Qt.KeyboardModifier(int(item) & ~0x01FFFFFF)
    if key in (
        int(Qt.Key_Control),
        int(Qt.Key_Shift),
        int(Qt.Key_Alt),
        int(Qt.Key_Meta),
        int(Qt.Key_unknown),
        int(Qt.Key_Escape),
    ):
        return None
    win_mod = 0
    if mods & Qt.KeyboardModifier.ControlModifier:
        win_mod |= MOD_CONTROL
    if mods & Qt.KeyboardModifier.AltModifier:
        win_mod |= MOD_ALT
    if mods & Qt.KeyboardModifier.ShiftModifier:
        win_mod |= MOD_SHIFT
    if mods & Qt.KeyboardModifier.MetaModifier:
        win_mod |= MOD_WIN
    if win_mod == 0:
        return None
    vk = _qt_key_to_vk(key)
    if vk is None:
        return None
    return win_mod, vk


def _qt_key_to_vk(key: int) -> int | None:
    if int(Qt.Key_A) <= key <= int(Qt.Key_Z):
        return key
    if int(Qt.Key_0) <= key <= int(Qt.Key_9):
        return key
    if int(Qt.Key_F1) <= key <= int(Qt.Key_F24):
        return 0x70 + (key - int(Qt.Key_F1))
    return _VK_EXTRA.get(key)


def _event_kind(event_type) -> str:
    if isinstance(event_type, str):
        return event_type
    if isinstance(event_type, (bytes, bytearray)):
        return event_type.decode("ascii", "ignore")
    data = getattr(event_type, "data", None)
    if callable(data):
        raw = data()
        if isinstance(raw, (bytes, bytearray)):
            return raw.decode("ascii", "ignore")
        if isinstance(raw, str):
            return raw
    try:
        return bytes(event_type).decode("ascii", "ignore")
    except (TypeError, ValueError):
        return str(event_type)


class _HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, owner: "HotkeyService"):
        super().__init__()
        self._owner = owner

    def nativeEventFilter(self, event_type, message):  # noqa: N802
        if sys.platform != "win32":
            return False, 0
        kind = _event_kind(event_type)
        if "MSG" not in kind:
            return False, 0
        try:
            msg = wintypes.MSG.from_address(int(message))
        except (TypeError, ValueError, OverflowError):
            return False, 0
        if msg.message == WM_HOTKEY:
            action = self._owner.action_for(int(msg.wParam))
            if action:
                self._owner.activated.emit(action)
                return True, 0
        return False, 0


class HotkeyService(QObject):
    activated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter = _HotkeyFilter(self)
        self._registered = False
        self._filter_installed = False
        self._id_to_action: dict[int, str] = {}

    def action_for(self, hot_id: int) -> str | None:
        return self._id_to_action.get(hot_id)

    def install(self, app, bindings: dict[str, str] | None = None) -> set[str]:
        if sys.platform != "win32":
            return set()
        self.uninstall()
        user32 = ctypes.windll.user32
        mapping = bindings or DEFAULT_HOTKEYS
        for action, sequence in mapping.items():
            hot_id = HOTKEY_IDS.get(action)
            parsed = parse_hotkey(sequence)
            if hot_id is None or parsed is None:
                continue
            mods, vk = parsed
            if user32.RegisterHotKey(None, hot_id, mods | MOD_NOREPEAT, vk):
                self._id_to_action[hot_id] = action
        if self._id_to_action and not self._filter_installed and app is not None:
            app.installNativeEventFilter(self._filter)
            self._filter_installed = True
        self._registered = True
        return set(self._id_to_action.values())

    def uninstall(self) -> None:
        if not self._registered and not self._id_to_action:
            return
        if sys.platform == "win32":
            user32 = ctypes.windll.user32
            for hot_id in list(self._id_to_action):
                user32.UnregisterHotKey(None, hot_id)
        self._id_to_action.clear()
        self._registered = False

    def registered_actions(self) -> set[str]:
        return set(self._id_to_action.values())
