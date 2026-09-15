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
    elif kind in {"sf-pin", "sf-pin-fill"}:
        p.save()
        p.translate(12, 12)
        p.rotate(30)
        p.translate(-12, -12)
        pin = QPainterPath()
        pin.moveTo(8, 5.5)
        pin.lineTo(16, 5.5)
        pin.lineTo(15, 11)
        pin.lineTo(18, 14)
        pin.lineTo(6, 14)
        pin.lineTo(9, 11)
        pin.closeSubpath()
        if kind == "sf-pin-fill":
            p.setBrush(c)
            p.drawPath(pin)
            p.setBrush(Qt.NoBrush)
        else:
            p.drawPath(pin)
        p.drawLine(QPointF(12, 14), QPointF(12, 20))
        p.restore()
    elif kind == "sf-palette":
        p.drawEllipse(QRectF(4.5, 4.5, 15, 15))
        p.drawEllipse(QRectF(7.4, 7.4, 1.8, 1.8))
        p.drawEllipse(QRectF(11.2, 6.6, 1.8, 1.8))
        p.drawEllipse(QRectF(14.7, 8.7, 1.8, 1.8))
        p.setPen(Qt.NoPen)
        p.setBrush(c)
        p.drawEllipse(QRectF(8.4, 13.2, 4.3, 3.6))
    elif kind == "sf-sliders":
        p.drawLine(QPointF(5, 7), QPointF(19, 7))
        p.drawLine(QPointF(5, 12), QPointF(19, 12))
        p.drawLine(QPointF(5, 17), QPointF(19, 17))
        p.setBrush(c)
        p.drawEllipse(QRectF(8, 5, 4, 4))
        p.drawEllipse(QRectF(13, 10, 4, 4))
        p.drawEllipse(QRectF(7, 15, 4, 4))
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
        disc = QRectF(4.4, 4.4, 15.2, 15.2)
        p.drawEllipse(disc)
        half = QPainterPath()
        half.moveTo(12, 4.4)
        half.arcTo(disc, 90, -180)
        half.closeSubpath()
        p.setBrush(c)
        p.setPen(Qt.NoPen)
        p.drawPath(half)
        p.setPen(_stroke(c, 1.85))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(disc)
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
    elif kind in {"pin-top", "keep-top"}:
        p.drawLine(QPointF(5.0, 5.0), QPointF(19.0, 5.0))
        p.drawLine(QPointF(12, 20.2), QPointF(12, 9.4))
        head = QPainterPath()
        head.moveTo(7.0, 13.8)
        head.lineTo(12, 7.4)
        head.lineTo(17.0, 13.8)
        if kind == "keep-top":
            head.closeSubpath()
            p.setBrush(c)
            p.drawPath(head)
            p.setBrush(Qt.NoBrush)
        else:
            p.drawPath(head)
    elif kind in {"pin", "pinned"}:
        p.save()
        p.translate(12, 12.6)
        p.rotate(28)
        p.translate(-12, -12)
        head = QPainterPath()
        head.addEllipse(QPointF(12, 6.2), 3.7, 3.7)
        cone = QPainterPath()
        cone.moveTo(8.6, 8.2)
        cone.lineTo(12, 16.0)
        cone.lineTo(15.4, 8.2)
        cone.closeSubpath()
        body = head.united(cone)
        if kind == "pinned":
            p.setBrush(c)
            p.setPen(_stroke(c, 1.7))
            p.drawPath(body)
            p.setBrush(Qt.NoBrush)
        else:
            p.drawPath(body)
        p.drawLine(QPointF(12, 15.8), QPointF(12, 20.8))
        p.restore()
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
    elif kind == "wrench":
        p.save()
        p.translate(12, 12)
        p.rotate(-40)
        p.drawRoundedRect(QRectF(-1.3, -1.5, 2.4, 11.5), 1.1, 1.1)
        p.drawRoundedRect(QRectF(-3.8, -8.6, 7.4, 6.6), 1.8, 1.8)
        p.restore()


def stroke_icon(kind: str, color: str, size: int = 18) -> QIcon:
    def draw(p: QPainter, s: int, c: QColor) -> None:
        _to_24(p, s)
        _draw_kind(p, kind, c)

    return QIcon(_pixmap(size, draw, color))
