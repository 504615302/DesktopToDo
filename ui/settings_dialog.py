from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from model.settings import AppSettings
from ui.datetime_picker import IconButton
from ui.icons import stroke_icon
from ui.styles import THEME_CHOICES, Theme, resolve_theme


class SettingsDialog(QDialog):
    opacity_previewed = Signal(float)
    theme_previewed = Signal(str)

    def __init__(self, theme: Theme, settings: AppSettings, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._settings = settings
        self._selected_theme = settings.theme
        self._drag_offset: QPoint | None = None
        self.setWindowTitle("设置")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(12)

        header = QHBoxLayout()
        heading = QLabel("设置")
        heading.setStyleSheet("font-size: 17px; font-weight: 600;")
        close_btn = IconButton("close", theme.text_muted, "关闭", 28, 14)
        close_btn.clicked.connect(self.reject)
        header.addWidget(heading)
        header.addStretch()
        header.addWidget(close_btn)
        layout.addLayout(header)

        self.lock_check = QCheckBox("锁定窗口位置")
        self.lock_check.setChecked(settings.lock_position)
        layout.addWidget(self.lock_check)

        self.auto_start_check = QCheckBox("开机自动启动")
        self.auto_start_check.setChecked(settings.auto_start)
        layout.addWidget(self.auto_start_check)

        self.top_check = QCheckBox("窗口始终置顶")
        self.top_check.setChecked(settings.always_on_top)
        layout.addWidget(self.top_check)

        layout.addWidget(self._label("主题风格"))
        self._theme_buttons: dict[str, QPushButton] = {}
        theme_grid = QGridLayout()
        theme_grid.setSpacing(8)
        for index, (label, value) in enumerate(THEME_CHOICES):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(40)
            sample = resolve_theme(value)
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background: {sample.surface};
                    color: {sample.text};
                    border: 1px solid {sample.border};
                    border-radius: {max(10, sample.chip_radius)}px;
                }}
                QPushButton:checked {{
                    border: 2px solid {sample.accent};
                    background: {sample.chip_active};
                    color: {sample.accent};
                    font-weight: 600;
                }}
                """
            )
            button.clicked.connect(lambda _checked=False, name=value: self._select_theme(name))
            theme_grid.addWidget(button, index // 2, index % 2)
            self._theme_buttons[value] = button
        layout.addLayout(theme_grid)
        self._refresh_theme_buttons()

        opacity_head = QHBoxLayout()
        opacity_head.addWidget(self._label("窗口透明度"))
        self.opacity_value = QLabel()
        self.opacity_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        opacity_head.addWidget(self.opacity_value)
        layout.addLayout(opacity_head)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(round(settings.opacity * 100)))
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        layout.addWidget(self.opacity_slider)
        self._on_opacity_changed(self.opacity_slider.value())

        hint = QLabel("锁定后窗口固定在桌面位置。置顶会盖住其他应用，默认关闭。")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {theme.text_muted}; font-size: 12px;")
        layout.addWidget(hint)

        self.ai_btn = QPushButton("AI 模型")
        self.template_btn = QPushButton("周报模板")
        self.support_btn = QPushButton("支持作者")
        self.ai_btn.setAutoDefault(False)
        self.template_btn.setAutoDefault(False)
        self.support_btn.setAutoDefault(False)
        self.support_btn.setIcon(stroke_icon("heart", theme.accent, 16))
        layout.addWidget(self.ai_btn)
        layout.addWidget(self.template_btn)
        layout.addWidget(self.support_btn)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("取消")
        save = QPushButton("保存")
        save.setObjectName("primaryButton")
        cancel.setFixedHeight(36)
        save.setFixedHeight(36)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -8)
        path = QPainterPath()
        path.addRoundedRect(rect, self._theme.radius, self._theme.radius)
        painter.fillPath(path, QColor(self._theme.bg))
        painter.setPen(QColor(self._theme.border))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.LeftButton and self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def _label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"color: {self._theme.text_secondary}; font-size: 12px; font-weight: 600;")
        return label

    def _select_theme(self, name: str) -> None:
        self._selected_theme = name
        self._refresh_theme_buttons()
        self.theme_previewed.emit(name)

    def _refresh_theme_buttons(self) -> None:
        for name, button in self._theme_buttons.items():
            button.setChecked(name == self._selected_theme)

    def _on_opacity_changed(self, value: int) -> None:
        self.opacity_value.setText(f"{value}%")
        self.opacity_previewed.emit(value / 100)

    def result_values(self) -> dict:
        return {
            "always_on_top": self.top_check.isChecked(),
            "lock_position": self.lock_check.isChecked(),
            "auto_start": self.auto_start_check.isChecked(),
            "theme": self._selected_theme,
            "opacity": self.opacity_slider.value() / 100,
        }
