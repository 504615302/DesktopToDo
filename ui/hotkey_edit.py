from __future__ import annotations

from PySide6.QtCore import QKeyCombination, Qt, Signal
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import QPushButton

from service.hotkey_service import normalize_hotkey, restore_ctrl_letter_key


class HotkeyEdit(QPushButton):
    changed = Signal(str)

    def __init__(self, sequence: str, parent=None):
        super().__init__(parent)
        self._sequence = normalize_hotkey(sequence, sequence) or sequence
        self._listening = False
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setAutoDefault(False)
        self.setDefault(False)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setFixedHeight(32)
        self.setMinimumWidth(132)
        self.clicked.connect(self._start_listen)
        self._render()

    def sequence(self) -> str:
        return self._sequence

    def set_sequence(self, sequence: str) -> None:
        self._sequence = sequence
        self._listening = False
        self.setChecked(False)
        self._render()

    def _start_listen(self) -> None:
        self._listening = True
        self.setChecked(True)
        self.setText("按下快捷键…")
        self.setFocus(Qt.MouseFocusReason)
        self.grabKeyboard()

    def _stop_listen(self) -> None:
        self._listening = False
        self.setChecked(False)
        self.releaseKeyboard()
        self._render()

    def _render(self) -> None:
        self.setText(self._sequence or "未设置")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self._listening:
            super().keyPressEvent(event)
            return
        if event.isAutoRepeat():
            event.accept()
            return
        key = event.key()
        mods = event.modifiers()
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            event.accept()
            return
        if key == Qt.Key_Escape and not (mods & Qt.ControlModifier):
            self._stop_listen()
            event.accept()
            return
        key = restore_ctrl_letter_key(key, mods, int(event.nativeVirtualKey()))
        combination = QKeyCombination(mods, Qt.Key(key))
        text = normalize_hotkey(QKeySequence(combination).toString(QKeySequence.PortableText))
        if not text:
            event.accept()
            return
        self._sequence = text
        self._stop_listen()
        self.changed.emit(text)
        event.accept()

    def focusOutEvent(self, event) -> None:
        if self._listening:
            self._stop_listen()
        super().focusOutEvent(event)
