from __future__ import annotations

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def _pixmap(size: int, draw, color: str) -> QPixmap:
    dpr = 2
    pm = QPixmap(size * dpr, size * dpr)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.scale(dpr, dpr)
    draw(painter, size, QColor(color))
    painter.end()
    pm.setDevicePixelRatio(dpr)
    return pm


def _pen(color: QColor, width: float = 1.6) -> QPen:
    pen = QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    return pen


def app_icon(size: int = 64) -> QIcon:
    def draw(p: QPainter, s: int, _color: QColor) -> None:
        radius = s * 0.22
        rect = QRectF(1, 1, s - 2, s - 2)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#4F46E5"))
        p.drawRoundedRect(rect, radius, radius)
        p.setPen(_pen(QColor("#FFFFFF"), s * 0.08))
        p.setBrush(Qt.NoBrush)
        path = QPainterPath()
        path.moveTo(s * 0.28, s * 0.52)
        path.lineTo(s * 0.44, s * 0.68)
        path.lineTo(s * 0.74, s * 0.34)
        p.drawPath(path)

    icon = QIcon()
    for value in (16, 32, 48, 64, 128, 256):
        icon.addPixmap(_pixmap(value, draw, "#4F46E5"))
    return icon


def stroke_icon(kind: str, color: str, size: int = 18) -> QIcon:
    def draw(p: QPainter, s: int, c: QColor) -> None:
        p.setPen(_pen(c, 1.7))
        p.setBrush(Qt.NoBrush)
        m = s * 0.22
        if kind == "close":
            p.drawLine(QPoint(int(m), int(m)), QPoint(int(s - m), int(s - m)))
            p.drawLine(QPoint(int(s - m), int(m)), QPoint(int(m), int(s - m)))
        elif kind == "minimize":
            y = int(s * 0.55)
            p.drawLine(QPoint(int(m), y), QPoint(int(s - m), y))
        elif kind == "settings":
            cx, cy, r = s / 2, s / 2, s * 0.16
            p.drawEllipse(QPoint(int(cx), int(cy)), int(r), int(r))
            for i in range(6):
                p.save()
                p.translate(cx, cy)
                p.rotate(i * 60)
                p.drawLine(QPoint(0, int(-s * 0.28)), QPoint(0, int(-s * 0.38)))
                p.restore()
        elif kind == "pin":
            p.drawLine(QPoint(int(s * 0.5), int(s * 0.22)), QPoint(int(s * 0.5), int(s * 0.72)))
            p.drawEllipse(QPoint(int(s * 0.5), int(s * 0.28)), int(s * 0.14), int(s * 0.14))
            p.drawLine(QPoint(int(s * 0.38), int(s * 0.78)), QPoint(int(s * 0.62), int(s * 0.78)))
        elif kind == "pinned":
            p.setBrush(c)
            p.drawEllipse(QPoint(int(s * 0.5), int(s * 0.32)), int(s * 0.16), int(s * 0.16))
            p.setBrush(Qt.NoBrush)
            p.drawLine(QPoint(int(s * 0.5), int(s * 0.48)), QPoint(int(s * 0.5), int(s * 0.78)))
        elif kind == "edit":
            p.drawLine(QPoint(int(s * 0.28), int(s * 0.72)), QPoint(int(s * 0.72), int(s * 0.28)))
            p.drawLine(QPoint(int(s * 0.28), int(s * 0.72)), QPoint(int(s * 0.22), int(s * 0.78)))
            p.drawLine(QPoint(int(s * 0.66), int(s * 0.22)), QPoint(int(s * 0.78), int(s * 0.34)))
        elif kind == "delete":
            p.drawRoundedRect(QRectF(s * 0.3, s * 0.36, s * 0.4, s * 0.42), 2, 2)
            p.drawLine(QPoint(int(s * 0.28), int(s * 0.36)), QPoint(int(s * 0.72), int(s * 0.36)))
            p.drawLine(QPoint(int(s * 0.38), int(s * 0.28)), QPoint(int(s * 0.62), int(s * 0.28)))

    return QIcon(_pixmap(size, draw, color))
