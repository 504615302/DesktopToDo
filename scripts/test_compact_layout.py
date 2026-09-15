from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.db import Database
from main import build_context
from ui.main_window import MainWindow
from ui.styles import build_stylesheet, resolve_theme


def test_compact_chat_keeps_full_input_area() -> None:
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    with TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        tmp = Path(temp_dir)
        database = Database(tmp / "todo.db")
        try:
            context = build_context(database, tmp / "settings.json")
            theme = resolve_theme(context.settings.settings.theme)
            app.setStyleSheet(build_stylesheet(theme))
            window = MainWindow(context)
            window.toggle_compact()
            app.processEvents()
            content_margins = window.content_shell.layout().contentsMargins()
            required = window.chat_page.compact_height() + content_margins.top() + content_margins.bottom()
            assert window.content_shell.height() >= required
            assert window.chat_page.input.isVisible()
            window.chat_page.input.setFocus()
            assert window.chat_page.input.hasFocus()
            window._really_quit = True
            window.close()
        finally:
            database.close()


if __name__ == "__main__":
    test_compact_chat_keeps_full_input_area()
    print("compact layout ok")
