"""Build app.ico from resources/icons/app.png for window/tray/PyInstaller."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QPixmap

ROOT = Path(__file__).resolve().parents[1]
SIZES = (16, 24, 32, 48, 64, 128, 256)


def png_bytes(pixmap: QPixmap) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    pixmap.save(buffer, "PNG")
    return bytes(data)


def write_ico(images: list[tuple[int, bytes]], dest: Path) -> None:
    count = len(images)
    header = struct.pack("<HHH", 0, 1, count)
    offset = 6 + 16 * count
    entries = bytearray()
    payload = bytearray()
    for size, data in images:
        width = 0 if size >= 256 else size
        height = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", width, height, 0, 0, 1, 32, len(data), offset)
        payload += data
        offset += len(data)
    dest.write_bytes(header + entries + payload)


def main() -> None:
    QGuiApplication.instance() or QGuiApplication([])
    icon_dir = ROOT / "resources" / "icons"
    png_path = icon_dir / "app.png"
    ico_path = icon_dir / "app.ico"
    if not png_path.exists():
        raise SystemExit(f"Missing source icon: {png_path}")
    source = QPixmap(str(png_path))
    if source.isNull():
        raise SystemExit(f"Could not read icon image: {png_path}")
    frames = [
        (size, png_bytes(source.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
        for size in SIZES
    ]
    write_ico(frames, ico_path)
    print(f"Wrote {ico_path}")


if __name__ == "__main__":
    main()
