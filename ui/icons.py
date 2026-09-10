from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

from app_paths import icon_path


def _pixmap(size: int, draw, color: str) -> QPixmap:
    dpr = 2
    pm = QPixmap(size * dpr, size * dpr)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    painter.scale(dpr, dpr)
    draw(painter, size, QColor(color))
    painter.end()
    pm.setDevicePixelRatio(dpr)
    return pm


def _stroke(color: QColor, width: float = 1.7) -> QPen:
    return QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)


def _to_24(painter: QPainter, size: int) -> None:
    pad = size * 0.12
    painter.translate(pad, pad)
    painter.scale((size - pad * 2) / 24.0, (size - pad * 2) / 24.0)


def app_icon(size: int = 64) -> QIcon:
    _ = size
    png = icon_path("app.png")
    ico = icon_path("app.ico")
    source = png if png.exists() else ico
    if source.exists():
        base = QPixmap(str(source))
        if not base.isNull():
            icon = QIcon()
            for value in (16, 32, 48, 64, 128, 256):
                icon.addPixmap(
                    base.scaled(value, value, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            return icon
    return _drawn_app_icon()


def asset_pixmap(name: str, size: int = 20, opacity: float = 1.0) -> QPixmap:
    path = icon_path(f"{name}.png")
    if not path.exists():
        return QPixmap()
    source = QPixmap(str(path))
    if source.isNull():
        return QPixmap()
    scaled = source.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    if opacity >= 0.99:
        return scaled
    faded = QPixmap(scaled.size())
    faded.fill(Qt.transparent)
    painter = QPainter(faded)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    painter.setOpacity(max(0.0, min(1.0, opacity)))
    painter.drawPixmap(0, 0, scaled)
    painter.end()
    return faded


def asset_icon(name: str, size: int = 20, opacity: float = 1.0) -> QIcon:
    pixmap = asset_pixmap(name, size, opacity)
    return QIcon(pixmap) if not pixmap.isNull() else QIcon()


def _drawn_app_icon() -> QIcon:
    def draw(p: QPainter, s: int, _color: QColor) -> None:
        rect = QRectF(1, 1, s - 2, s - 2)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#3B82F6"))
        p.drawRoundedRect(rect, s * 0.24, s * 0.24)
        p.setPen(_stroke(QColor("#FFFFFF"), s * 0.075))
        p.setBrush(Qt.NoBrush)
        box = QRectF(s * 0.28, s * 0.30, s * 0.44, s * 0.44)
        p.drawRoundedRect(box, s * 0.06, s * 0.06)
        p.drawLine(QPointF(s * 0.38, s * 0.30), QPointF(s * 0.38, s * 0.24))
        p.drawLine(QPointF(s * 0.62, s * 0.30), QPointF(s * 0.62, s * 0.24))
        p.drawLine(QPointF(s * 0.28, s * 0.42), QPointF(s * 0.72, s * 0.42))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QPointF(s * 0.50, s * 0.58), s * 0.045, s * 0.045)

    icon = QIcon()
    for value in (16, 32, 48, 64, 128, 256):
        icon.addPixmap(_pixmap(value, draw, "#3B82F6"))
    return icon


def _draw_kind(p: QPainter, kind: str, c: QColor) -> None:
    p.setPen(_stroke(c, 1.85))
    p.setBrush(Qt.NoBrush)

    if kind == "close":
        p.drawLine(QPointF(6, 6), QPointF(18, 18))
        p.drawLine(QPointF(18, 6), QPointF(6, 18))
    elif kind == "minimize":
        p.drawLine(QPointF(5, 12), QPointF(19, 12))
    elif kind == "collapse":
        p.drawRoundedRect(QRectF(4.5, 5, 15, 14), 2.2, 2.2)
        p.drawLine(QPointF(4.5, 15.5), QPointF(19.5, 15.5))
        path = QPainterPath()
        path.moveTo(8.2, 10.2)
        path.lineTo(12, 13.6)
        path.lineTo(15.8, 10.2)
        p.drawPath(path)
    elif kind == "expand":
        p.drawRoundedRect(QRectF(4.5, 4.5, 15, 15), 2.2, 2.2)
        p.drawLine(QPointF(4.5, 9), QPointF(19.5, 9))
        path = QPainterPath()
        path.moveTo(8.2, 14.8)
        path.lineTo(12, 11.4)
        path.lineTo(15.8, 14.8)
        p.drawPath(path)
    elif kind == "settings":
        p.drawEllipse(QPointF(12, 12), 3.2, 3.2)
        for angle in range(0, 360, 60):
            p.save()
            p.translate(12, 12)
            p.rotate(angle)
            p.drawLine(QPointF(0, -6.2), QPointF(0, -8.6))
            p.restore()
    elif kind == "lock":
        p.drawRoundedRect(QRectF(7, 11, 10, 8), 1.8, 1.8)
        path = QPainterPath()
        path.moveTo(9, 11)
        path.lineTo(9, 8.2)
        path.arcTo(QRectF(9, 5.4, 6, 5.6), 180, -180)
        path.lineTo(15, 11)
        p.drawPath(path)
    elif kind == "unlock":
        p.drawRoundedRect(QRectF(7, 11, 10, 8), 1.8, 1.8)
        path = QPainterPath()
        path.moveTo(9, 11)
        path.lineTo(9, 8.2)
        path.arcTo(QRectF(9, 5.4, 6, 5.6), 180, -180)
        p.drawPath(path)
    elif kind == "theme":
        p.drawRoundedRect(QRectF(4.2, 4.2, 7.2, 7.2), 1.6, 1.6)
        p.drawRoundedRect(QRectF(12.6, 4.2, 7.2, 7.2), 1.6, 1.6)
        p.drawRoundedRect(QRectF(4.2, 12.6, 7.2, 7.2), 1.6, 1.6)
        p.setBrush(c)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(12.6, 12.6, 7.2, 7.2), 1.6, 1.6)
        p.setPen(_stroke(c, 1.85))
        p.setBrush(Qt.NoBrush)
    elif kind == "edit":
        path = QPainterPath()
        path.moveTo(5, 19)
        path.lineTo(6.2, 14.6)
        path.lineTo(16.8, 4)
        path.lineTo(20, 7.2)
        path.lineTo(9.4, 17.8)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(14.6, 6.2), QPointF(17.8, 9.4))
    elif kind == "delete":
        p.drawRoundedRect(QRectF(6.5, 8.5, 11, 12), 1.6, 1.6)
        p.drawLine(QPointF(9.5, 11.2), QPointF(9.5, 17.2))
        p.drawLine(QPointF(12, 11.2), QPointF(12, 17.2))
        p.drawLine(QPointF(14.5, 11.2), QPointF(14.5, 17.2))
        p.drawLine(QPointF(5, 8.5), QPointF(19, 8.5))
        path = QPainterPath()
        path.moveTo(9, 8.5)
        path.lineTo(9.6, 5.8)
        path.lineTo(14.4, 5.8)
        path.lineTo(15, 8.5)
        p.drawPath(path)
    elif kind == "calendar":
        p.drawRoundedRect(QRectF(4, 6, 16, 14.5), 2.2, 2.2)
        p.drawLine(QPointF(4, 10.5), QPointF(20, 10.5))
        p.drawLine(QPointF(8, 4.2), QPointF(8, 7.8))
        p.drawLine(QPointF(16, 4.2), QPointF(16, 7.8))
        p.setPen(Qt.NoPen)
        p.setBrush(c)
        for x, y in ((8, 13.4), (12, 13.4), (16, 13.4), (8, 16.6), (12, 16.6)):
            p.drawEllipse(QPointF(x, y), 0.85, 0.85)
    elif kind == "chevron-left":
        path = QPainterPath()
        path.moveTo(14.5, 6)
        path.lineTo(8.5, 12)
        path.lineTo(14.5, 18)
        p.drawPath(path)
    elif kind == "chevron-right":
        path = QPainterPath()
        path.moveTo(9.5, 6)
        path.lineTo(15.5, 12)
        path.lineTo(9.5, 18)
        p.drawPath(path)
    elif kind == "chevron-up":
        path = QPainterPath()
        path.moveTo(6, 14.5)
        path.lineTo(12, 8.5)
        path.lineTo(18, 14.5)
        p.drawPath(path)
    elif kind == "chevron-down":
        path = QPainterPath()
        path.moveTo(6, 9.5)
        path.lineTo(12, 15.5)
        path.lineTo(18, 9.5)
        p.drawPath(path)
    elif kind == "clock":
        p.drawEllipse(QRectF(4, 4, 16, 16))
        p.drawLine(QPointF(12, 12), QPointF(12, 8.2))
        p.drawLine(QPointF(12, 12), QPointF(16, 13.6))
    elif kind == "bell":
        path = QPainterPath()
        path.moveTo(6.5, 16)
        path.lineTo(6.5, 11)
        path.quadTo(6.5, 6.2, 12, 6.2)
        path.quadTo(17.5, 6.2, 17.5, 11)
        path.lineTo(17.5, 16)
        path.lineTo(19, 18)
        path.lineTo(5, 18)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(10.2, 19.4), QPointF(13.8, 19.4))
    elif kind == "plus":
        p.drawLine(QPointF(12, 6), QPointF(12, 18))
        p.drawLine(QPointF(6, 12), QPointF(18, 12))
    elif kind == "flag":
        path = QPainterPath()
        path.moveTo(7, 20)
        path.lineTo(7, 4.5)
        path.lineTo(18, 9.2)
        path.lineTo(7, 13.8)
        p.drawPath(path)
    elif kind == "check":
        path = QPainterPath()
        path.moveTo(5, 12.2)
        path.lineTo(10, 17)
        path.lineTo(19, 7)
        p.drawPath(path)
    elif kind in {"pin", "pinned"}:
        path = QPainterPath()
        path.moveTo(12, 4)
        path.lineTo(15.8, 10.2)
        path.lineTo(18, 10.2)
        path.lineTo(13.3, 13)
        path.lineTo(14.6, 20)
        path.lineTo(12, 17.4)
        path.lineTo(9.4, 20)
        path.lineTo(10.7, 13)
        path.lineTo(6, 10.2)
        path.lineTo(8.2, 10.2)
        path.closeSubpath()
        if kind == "pinned":
            p.setBrush(c)
            p.setPen(Qt.NoPen)
        p.drawPath(path)
    elif kind == "search":
        p.drawEllipse(QRectF(5, 5, 10.5, 10.5))
        p.drawLine(QPointF(13.4, 13.4), QPointF(18.5, 18.5))
    elif kind == "copy":
        p.drawRoundedRect(QRectF(8, 8, 10, 12), 1.6, 1.6)
        p.drawRoundedRect(QRectF(5, 4, 10, 12), 1.6, 1.6)
    elif kind == "sparkle":
        p.drawLine(QPointF(12, 4), QPointF(12, 9))
        p.drawLine(QPointF(9.5, 6.5), QPointF(14.5, 6.5))
        p.drawLine(QPointF(6, 13), QPointF(10, 17))
        p.drawLine(QPointF(6, 17), QPointF(10, 13))
        p.drawLine(QPointF(15.5, 12.5), QPointF(18.5, 18))
        p.drawLine(QPointF(15.5, 18), QPointF(18.5, 12.5))
    elif kind == "note":
        p.drawRoundedRect(QRectF(5.5, 4, 13, 16), 1.8, 1.8)
        p.drawLine(QPointF(8.5, 9), QPointF(15.5, 9))
        p.drawLine(QPointF(8.5, 12.5), QPointF(15.5, 12.5))
        p.drawLine(QPointF(8.5, 16), QPointF(13, 16))
    elif kind == "chat":
        p.drawRoundedRect(QRectF(4.2, 4.5, 15.6, 11.8), 2.4, 2.4)
        path = QPainterPath()
        path.moveTo(8, 16)
        path.lineTo(6.8, 20)
        path.lineTo(12.2, 16)
        p.drawPath(path)
    elif kind == "heart":
        path = QPainterPath()
        path.moveTo(12, 19)
        path.cubicTo(6.2, 14.6, 4.2, 10.8, 4.2, 8.2)
        path.cubicTo(4.2, 5.8, 6.1, 4.2, 8.4, 4.2)
        path.cubicTo(10, 4.2, 11.3, 5.1, 12, 6.4)
        path.cubicTo(12.7, 5.1, 14, 4.2, 15.6, 4.2)
        path.cubicTo(17.9, 4.2, 19.8, 5.8, 19.8, 8.2)
        path.cubicTo(19.8, 10.8, 17.8, 14.6, 12, 19)
        path.closeSubpath()
        p.drawPath(path)


def stroke_icon(kind: str, color: str, size: int = 18) -> QIcon:
    def draw(p: QPainter, s: int, c: QColor) -> None:
        _to_24(p, s)
        _draw_kind(p, kind, c)

    return QIcon(_pixmap(size, draw, color))
