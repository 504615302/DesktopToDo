from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QPlainTextEdit, QPushButton

from model.task import Task
from ui.framed_dialog import FramedDialog
from ui.styles import Theme


class WorkResultDialog(FramedDialog):
    def __init__(self, theme: Theme, task: Task, parent=None):
        super().__init__(theme, "记录工作结果", parent, width=420)
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("联调完成。已统一接口字段格式…")
        self.editor.setMinimumHeight(140)
        self.report_check = QCheckBox("加入本周周报素材")
        self.report_check.setChecked(True)
        save = QPushButton("保存为备忘")
        save.setObjectName("primaryButton")
        save.setFixedHeight(36)
        save.clicked.connect(self.accept)
        self.root.addWidget(self.caption(task.title))
        self.root.addWidget(self.editor)
        self.root.addWidget(self.report_check)
        self.root.addWidget(save)
        self.editor.setFocus()

    def result_values(self) -> tuple[str, bool]:
        return self.editor.toPlainText().strip(), self.report_check.isChecked()
