from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from model.task import Task
from ui.styles import Theme


class TaskDialog(QDialog):
    def __init__(self, theme: Theme, task: Task | None = None, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._task = task
        self.setWindowTitle("编辑任务" if task else "新建任务")
        self.setModal(True)
        self.setMinimumWidth(360)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self._build()
        if task:
            self.title_edit.setText(task.title)
            self.desc_edit.setPlainText(task.description)
            self.priority_combo.setCurrentIndex(task.priority_enum.value)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(10)

        heading = QLabel("编辑任务" if self._task else "新建任务")
        heading.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(heading)

        layout.addWidget(self._label("任务名称"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("输入任务名称")
        layout.addWidget(self.title_edit)

        layout.addWidget(self._label("任务描述"))
        self.desc_edit = QPlainTextEdit()
        self.desc_edit.setPlaceholderText("可选，补充说明")
        self.desc_edit.setFixedHeight(90)
        layout.addWidget(self.desc_edit)

        layout.addWidget(self._label("优先级"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["普通", "重要", "紧急"])
        layout.addWidget(self.priority_combo)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("取消")
        save = QPushButton("保存")
        save.setObjectName("primaryButton")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)
        self.title_edit.setFocus()

    def _label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"color: {self._theme.text_secondary}; font-size: 12px;")
        return label

    def result_values(self) -> tuple[str, str, int]:
        return (
            self.title_edit.text().strip(),
            self.desc_edit.toPlainText().strip(),
            self.priority_combo.currentIndex(),
        )
