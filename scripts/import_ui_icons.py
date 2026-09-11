"""Knock out black backgrounds and copy UI icons into resources/icons."""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

from PySide6.QtGui import QColor, QGuiApplication, QImage

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path(r"C:\Users\50461\.cursor\projects\d-DesktopToDo-DesktopToDo\assets")
DEST = ROOT / "resources" / "icons"

ICONS = {
    "action_pin.png": "c__Users_50461_AppData_Roaming_Cursor_User_workspaceStorage_532faae449f0e1b21427a9d7ff817853_images___-129f2e59-211a-4d4e-8df8-470fb3b26b04.png",
    "nav_todo.png": "c__Users_50461_AppData_Roaming_Cursor_User_workspaceStorage_532faae449f0e1b21427a9d7ff817853_images____-aae41c65-87f4-4ab6-b4d4-15fe6d50607c.png",
    "nav_memo.png": "c__Users_50461_AppData_Roaming_Cursor_User_workspaceStorage_532faae449f0e1b21427a9d7ff817853_images___-ec15c178-ebeb-4a09-af75-faf1b6d424d6.png",
    "priority.png": "c__Users_50461_AppData_Roaming_Cursor_User_workspaceStorage_532faae449f0e1b21427a9d7ff817853_images_____-6e8f8c95-b975-4d37-bf44-ef9a7ea53e83.png",
    "nav_report.png": "c__Users_50461_AppData_Roaming_Cursor_User_workspaceStorage_532faae449f0e1b21427a9d7ff817853_images____-e0f2fc3f-4b4f-43f3-8b5e-f0ab7b1ab01e.png",
    "nav_today.png": "c__Users_50461_AppData_Roaming_Cursor_User_workspaceStorage_532faae449f0e1b21427a9d7ff817853_images_____-01-e811b8d1-210e-40cc-b98a-d3b5732dbb3a.png",
    "action_settings.png": "c__Users_50461_AppData_Roaming_Cursor_User_workspaceStorage_532faae449f0e1b21427a9d7ff817853_images___-e259b040-96e3-4190-bc87-6bde2bb386f1.png",
    "nav_chat.png": "c__Users_50461_AppData_Roaming_Cursor_User_workspaceStorage_532faae449f0e1b21427a9d7ff817853_images_AI__-720dda6b-44a3-4b36-b5e1-52d96e173304.png",
    "action_theme.png": "c__Users_50461_AppData_Roaming_Cursor_User_workspaceStorage_532faae449f0e1b21427a9d7ff817853_images___-ca94916c-0d73-46e7-a8d5-af151ec6d5ca.png",
    "nav_tools.png": "c__Users_50461_AppData_Roaming_Cursor_User_workspaceStorage_532faae449f0e1b21427a9d7ff817853_images____-__-0-554e3947-d813-4d5e-b0aa-75c4b049d297.png",
}


def _is_key(color: QColor, threshold: int = 36) -> bool:
    return color.red() <= threshold and color.green() <= threshold and color.blue() <= threshold and color.alpha() > 0


def knock_out_black(image: QImage) -> QImage:
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
        if not _is_key(color):
            continue
        color.setAlpha(0)
        img.setPixelColor(x, y, color)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return img


def main() -> None:
    QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    DEST.mkdir(parents=True, exist_ok=True)
    for dest_name, source_name in ICONS.items():
        source = ASSETS / source_name
        if not source.exists():
            raise SystemExit(f"Missing {source}")
        image = QImage(str(source))
        if image.isNull():
            raise SystemExit(f"Could not read {source}")
        knock_out_black(image).save(str(DEST / dest_name), "PNG")
        print(f"Wrote {DEST / dest_name}")


if __name__ == "__main__":
    main()
