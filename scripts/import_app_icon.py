"""Turn the circular dog portrait into a transparent app.png."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPainterPath

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path(r"C:\Users\50461\.cursor\projects\d-DesktopToDo-DesktopToDo\assets")
SOURCE = ASSETS / "c__Users_50461_AppData_Roaming_Cursor_User_workspaceStorage_532faae449f0e1b21427a9d7ff817853_images_ChatGPT_Image_2026_9_10__16_10_47-330670b8-d7b2-42af-9583-2421ce25b442.jpg"
DEST = ROOT / "resources" / "icons" / "app.png"


def _is_black(color: QColor, threshold: int = 28) -> bool:
    return color.red() <= threshold and color.green() <= threshold and color.blue() <= threshold


def _circle(image: QImage) -> tuple[float, float, float]:
    width, height = image.width(), image.height()
    cx, cy = width / 2.0, height / 2.0
    left = 0
    for x in range(width):
        if not _is_black(QColor.fromRgba(image.pixel(x, int(cy)))):
            left = x
            break
    return cx, cy, max(8.0, cx - left - 1.5)


def main() -> None:
    QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    if not SOURCE.exists():
        raise SystemExit(f"Missing {SOURCE}")
    image = QImage(str(SOURCE))
    if image.isNull():
        raise SystemExit(f"Could not read {SOURCE}")

    cx, cy, radius = _circle(image)
    size = int(round(radius * 2))
    out = QImage(size, size, QImage.Format_ARGB32)
    out.fill(Qt.transparent)
    painter = QPainter(out)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    path = QPainterPath()
    path.addEllipse(QRectF(0.5, 0.5, size - 1, size - 1))
    painter.setClipPath(path)
    painter.drawImage(
        QRectF(0, 0, size, size),
        image,
        QRectF(cx - radius, cy - radius, radius * 2, radius * 2),
    )
    painter.end()

    DEST.parent.mkdir(parents=True, exist_ok=True)
    out.save(str(DEST), "PNG")
    print(f"Wrote {DEST} ({size}x{size})")


if __name__ == "__main__":
    main()
