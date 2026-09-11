from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton

from ui.framed_dialog import FramedDialog
from ui.styles import Theme
from ui.submit_edit import SubmitTextEdit


class QuickInputDialog(FramedDialog):
    def __init__(self, theme: Theme, title: str, placeholder: str, parent=None):
        super().__init__(theme, title, parent, width=360)
        self.edit = SubmitTextEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setFixedHeight(96)
        self.edit.submit_requested.connect(self.accept)
        hint = QLabel("Enter 换行，Ctrl+Enter 保存")
        hint.setStyleSheet(f"color: {theme.text_muted}; font-size: 12px;")
        save = QPushButton("保存")
        save.setObjectName("primaryButton")
        save.setFixedHeight(34)
        save.clicked.connect(self.accept)
        self.root.addWidget(self.edit)
        self.root.addWidget(hint)
        self.root.addWidget(save)
        self.edit.setFocus()

    def text(self) -> str:
        return self.edit.toPlainText().strip()
