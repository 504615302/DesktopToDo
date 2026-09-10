from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtWidgets import QApplication, QSystemTrayIcon

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.db import Database
from main import build_context
from ui.main_window import MainWindow
from ui.styles import build_stylesheet, resolve_theme


def test_window_builds() -> None:
    tmp_dir = TemporaryDirectory(ignore_cleanup_errors=True)
    tmp = Path(tmp_dir.name)
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    database = Database(tmp / "todo.db")
    try:
        ctx = build_context(database, tmp / "settings.json")
        theme = resolve_theme(ctx.settings.settings.theme)
        app.setStyleSheet(build_stylesheet(theme))
        window = MainWindow(ctx)
        assert window.windowTitle() == "DesktopToDo"
        window.task_service.add_task("窗口冒烟测试")
        window.reload_all()
        titles = [item.task.title for item in window.today_page._items + window.todo_page._items]
        assert "窗口冒烟测试" in titles
        assert window.stack.count() == 5
        window.toggle_compact()
        app.processEvents()
        assert window._compact is True
        assert window.chat_page._compact is True
        assert window.height() < 320
        window.toggle_compact()
        app.processEvents()
        assert window._compact is False
        dialog = window.chat_page
        dialog._refresh_model_button()
        assert "选择模型" in dialog.model_btn.text() or "·" in dialog.model_btn.text()
        from ui.chat_model_dialog import ChatModelDialog

        picker = ChatModelDialog(theme, ctx.reports, None, 0.3, 1024, window)
        assert picker.windowTitle() == "问答模型"
        picker.close()
        if QSystemTrayIcon.isSystemTrayAvailable():
            assert window.tray.isVisible()
        window._really_quit = True
        window.close()
    finally:
        database.close()
        tmp_dir.cleanup()


if __name__ == "__main__":
    test_window_builds()
    print("ui ok")
