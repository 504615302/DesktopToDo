from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QPushButton

from ui.framed_dialog import FramedDialog
from ui.styles import Theme


class QuickNoteTextEdit(QPlainTextEdit):
    save_requested = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and event.modifiers() & Qt.ShiftModifier:
            self.save_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class QuickInputDialog(FramedDialog):
    def __init__(self, theme: Theme, title: str, placeholder: str, parent=None):
        super().__init__(theme, title, parent, width=360)
        self.edit = QuickNoteTextEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setFixedHeight(96)
        self.edit.save_requested.connect(self._accept_if_not_empty)
        hint = QLabel("Enter 换行，Shift+Enter 保存")
        hint.setStyleSheet(f"color: {theme.text_muted}; font-size: 12px;")
        save = QPushButton("保存")
        save.setObjectName("primaryButton")
        save.setFixedHeight(34)
        save.clicked.connect(self._accept_if_not_empty)
        self.root.addWidget(self.edit)
        self.root.addWidget(hint)
        self.root.addWidget(save)
        self.edit.setFocus()

    def text(self) -> str:
        return self.edit.toPlainText().strip()

    def _accept_if_not_empty(self) -> None:
        if self.text():
            self.accept()
