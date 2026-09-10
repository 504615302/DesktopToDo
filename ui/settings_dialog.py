from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from model.settings import AppSettings
from ui.styles import Theme

OPACITY_CHOICES = [("100%", 1.0), ("90%", 0.9), ("80%", 0.8), ("70%", 0.7)]
THEME_CHOICES = [("浅色模式", "light"), ("深色模式", "dark"), ("跟随 Windows", "system")]


class SettingsDialog(QDialog):
    def __init__(self, theme: Theme, settings: AppSettings, parent=None):
        super().__init__(parent)
        self._theme = theme
        self.setWindowTitle("设置")
        self.setModal(True)
        self.setMinimumWidth(340)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(12)

        heading = QLabel("设置")
        heading.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(heading)

        self.top_check = QCheckBox("窗口始终置顶")
        self.top_check.setChecked(settings.always_on_top)
        layout.addWidget(self.top_check)

        self.auto_start_check = QCheckBox("开机自动启动")
        self.auto_start_check.setChecked(settings.auto_start)
        layout.addWidget(self.auto_start_check)

        layout.addWidget(self._label("主题"))
        self.theme_combo = QComboBox()
        for label, value in THEME_CHOICES:
            self.theme_combo.addItem(label, value)
        index = max(0, self.theme_combo.findData(settings.theme))
        self.theme_combo.setCurrentIndex(index)
        layout.addWidget(self.theme_combo)

        layout.addWidget(self._label("窗口透明度"))
        self.opacity_combo = QComboBox()
        current = min(OPACITY_CHOICES, key=lambda item: abs(item[1] - settings.opacity))
        for label, value in OPACITY_CHOICES:
            self.opacity_combo.addItem(label, value)
        self.opacity_combo.setCurrentIndex(OPACITY_CHOICES.index(current))
        layout.addWidget(self.opacity_combo)

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

    def _label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"color: {self._theme.text_secondary}; font-size: 12px;")
        return label

    def result_values(self) -> dict:
        return {
            "always_on_top": self.top_check.isChecked(),
            "auto_start": self.auto_start_check.isChecked(),
            "theme": self.theme_combo.currentData(),
            "opacity": float(self.opacity_combo.currentData()),
        }
