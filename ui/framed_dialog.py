from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPainterPath
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from ui.datetime_picker import IconButton
from ui.styles import Theme


class FramedDialog(QDialog):
    def __init__(self, theme: Theme, title: str, parent=None, width: int = 420):
        super().__init__(parent)
        self._theme = theme
        self._drag_offset: QPoint | None = None
        self.setModal(True)
        self.setMinimumWidth(width)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(28, 22, 28, 22)
        self.root.setSpacing(12)
        header = QHBoxLayout()
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 17px; font-weight: 600;")
        close_btn = IconButton("close", theme.text_muted, "关闭", 28, 14)
        close_btn.clicked.connect(self.reject)
        header.addWidget(heading)
        header.addStretch()
        header.addWidget(close_btn)
        self.root.addLayout(header)

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

    def caption(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"color: {self._theme.text_secondary}; font-size: 12px; font-weight: 600;")
        return label
