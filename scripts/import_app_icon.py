"""Turn the dog-and-checklist artwork into a transparent app.png."""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path(r"C:\Users\50461\.cursor\projects\d-DesktopToDo-DesktopToDo\assets")
SOURCE = ASSETS / "c__Users_50461_AppData_Roaming_Cursor_User_workspaceStorage_532faae449f0e1b21427a9d7ff817853_images_ChatGPT_Image_2026_9_11__17_03_04-fcc9a5ce-86e5-426c-99c3-cc5b7ac412f0.jpg"
DEST = ROOT / "resources" / "icons" / "app.png"


def _is_white(color: QColor, threshold: int = 248) -> bool:
    return color.red() >= threshold and color.green() >= threshold and color.blue() >= threshold


def knock_out_white(image: QImage) -> QImage:
    img = image.convertToFormat(QImage.Format_ARGB32)
    width, height = img.width(), img.height()
    seen = [False] * (width * height)
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))
    while queue:
        x, y = queue.popleft()
        if x < 0 or y < 0 or x >= width or y >= height:
            continue
        index = y * width + x
        if seen[index]:
            continue
        seen[index] = True
        color = QColor.fromRgba(img.pixel(x, y))
        if not _is_white(color):
            continue
        color.setAlpha(0)
        img.setPixelColor(x, y, color)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return img


def crop_opaque(image: QImage, pad: int = 2) -> QImage:
    width, height = image.width(), image.height()
    left, top, right, bottom = width, height, -1, -1
    for y in range(height):
        for x in range(width):
            if QColor.fromRgba(image.pixel(x, y)).alpha() < 16:
                continue
            left = min(left, x)
            right = max(right, x)
            top = min(top, y)
            bottom = max(bottom, y)
    if right < left:
        return image
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(width - 1, right + pad)
    bottom = min(height - 1, bottom + pad)
    size = max(right - left + 1, bottom - top + 1)
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    x0 = int(round(cx - size / 2))
    y0 = int(round(cy - size / 2))
    x0 = min(max(0, x0), width - size)
    y0 = min(max(0, y0), height - size)
    return image.copy(QRect(x0, y0, size, size))


def main() -> None:
    QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    if not SOURCE.exists():
        raise SystemExit(f"Missing {SOURCE}")
    image = QImage(str(SOURCE))
    if image.isNull():
        raise SystemExit(f"Could not read {SOURCE}")

    out = crop_opaque(knock_out_white(image))
    DEST.parent.mkdir(parents=True, exist_ok=True)
    out.save(str(DEST), "PNG")
    print(f"Wrote {DEST} ({out.width()}x{out.height()})")


if __name__ == "__main__":
    main()
