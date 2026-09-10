from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QGuiApplication, QMouseEvent, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget

from ui.styles import Theme

MARGIN = 10
RESIZE_BORDER = 8


class CardWindow(QWidget):
    def __init__(self, theme: Theme, resizable: bool = True, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._resizable = resizable
        self._locked = False
        self._drag_pos: QPoint | None = None
        self._resize_dir = ""
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window | Qt.Tool)
        extra = MARGIN * 2
        if resizable:
            self.setMinimumSize(360 + extra, 480 + extra)
        else:
            self.setMinimumSize(260 + extra, 160 + extra)

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.update()

    def set_locked(self, locked: bool) -> None:
        self._locked = locked
        if locked:
            self.setCursor(Qt.ArrowCursor)

    def apply_flags(self, always_on_top: bool = False) -> None:
        flags = Qt.FramelessWindowHint | Qt.Window | Qt.Tool
        if always_on_top:
            flags |= Qt.WindowStaysOnTopHint
        visible = self.isVisible()
        self.setWindowFlags(flags)
        if visible:
            self.show()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(MARGIN, MARGIN, -MARGIN, -MARGIN)
        shadow = QColor(self._theme.shadow)
        for i, alpha in enumerate((18, 12, 7, 3)):
            shadow.setAlpha(alpha)
            painter.setPen(Qt.NoPen)
            painter.setBrush(shadow)
            painter.drawRoundedRect(
                rect.adjusted(-i, -i + 1, i, i + 1),
                self._theme.radius + i,
                self._theme.radius + i,
            )

        radius = self._theme.radius
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.fillPath(path, QColor(self._theme.bg))
        painter.setPen(QColor(self._theme.border))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

    def inner_margins(self) -> tuple[int, int, int, int]:
        return (MARGIN, MARGIN, MARGIN, MARGIN)

    def _hit_resize_dir(self, pos: QPoint) -> str:
        if not self._resizable or self._locked:
            return ""
        rect = self.rect().adjusted(MARGIN, MARGIN, -MARGIN, -MARGIN)
        x, y = pos.x(), pos.y()
        left = abs(x - rect.left()) <= RESIZE_BORDER
        right = abs(x - rect.right()) <= RESIZE_BORDER
        top = abs(y - rect.top()) <= RESIZE_BORDER
        bottom = abs(y - rect.bottom()) <= RESIZE_BORDER
        if top and left:
            return "tl"
        if top and right:
            return "tr"
        if bottom and left:
            return "bl"
        if bottom and right:
            return "br"
        if left:
            return "l"
        if right:
            return "r"
        if top:
            return "t"
        if bottom:
            return "b"
        return ""

    def _cursor_for(self, direction: str):
        mapping = {
            "l": Qt.SizeHorCursor,
            "r": Qt.SizeHorCursor,
            "t": Qt.SizeVerCursor,
            "b": Qt.SizeVerCursor,
            "tl": Qt.SizeFDiagCursor,
            "br": Qt.SizeFDiagCursor,
            "tr": Qt.SizeBDiagCursor,
            "bl": Qt.SizeBDiagCursor,
        }
        return mapping.get(direction, Qt.ArrowCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._resize_dir = self._hit_resize_dir(event.position().toPoint())
            self._drag_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        if event.buttons() & Qt.LeftButton and self._drag_pos is not None:
            if self._resize_dir:
                self._resize_to(event.globalPosition().toPoint())
            elif self._can_drag():
                delta = event.globalPosition().toPoint() - self._drag_pos
                self._drag_pos = event.globalPosition().toPoint()
                self.move(self.pos() + delta)
        else:
            self.setCursor(self._cursor_for(self._hit_resize_dir(pos)))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None
        self._resize_dir = ""
        super().mouseReleaseEvent(event)

    def _can_drag(self) -> bool:
        return not self._locked

    def _resize_to(self, global_pos: QPoint) -> None:
        if self._drag_pos is None:
            return
        delta = global_pos - self._drag_pos
        geo = self.geometry()
        min_w, min_h = self.minimumWidth(), self.minimumHeight()
        direction = self._resize_dir
        x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()
        if "r" in direction:
            w = max(min_w, w + delta.x())
        if "b" in direction:
            h = max(min_h, h + delta.y())
        if "l" in direction:
            new_w = max(min_w, w - delta.x())
            x += w - new_w
            w = new_w
        if "t" in direction:
            new_h = max(min_h, h - delta.y())
            y += h - new_h
            h = new_h
        self.setGeometry(QRect(x, y, w, h))
        self._drag_pos = global_pos

    def clamp_to_screens(self) -> None:
        geo = self.frameGeometry()
        screens = QGuiApplication.screens()
        if not screens:
            return
        if any(screen.availableGeometry().intersects(geo) for screen in screens):
            return
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.move(
            screen.right() - geo.width() - 24,
            screen.top() + 48,
        )
