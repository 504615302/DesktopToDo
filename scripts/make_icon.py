"""Render the app icon to PNG and ICO for window/tray/PyInstaller."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication

from ui.icons import app_icon


def png_to_ico(png_bytes: bytes, dest: Path) -> None:
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png_bytes), 22)
    dest.write_bytes(header + entry + png_bytes)


def main() -> None:
    app = QApplication.instance() or QApplication([])
    icon_dir = ROOT / "resources" / "icons"
    icon_dir.mkdir(parents=True, exist_ok=True)
    pixmap = app_icon().pixmap(256, 256)
    png_path = icon_dir / "app.png"
    ico_path = icon_dir / "app.ico"
    pixmap.save(str(png_path), "PNG")
    png_to_ico(png_path.read_bytes(), ico_path)
    print(f"Wrote {png_path}")
    print(f"Wrote {ico_path}")
    if app is QApplication.instance() and not QApplication.instance().startingUp():
        pass


if __name__ == "__main__":
    main()
