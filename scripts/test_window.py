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
        assert window.windowTitle() == "桌面代办"
        window.task_service.add_task("窗口冒烟测试")
        window.reload_all()
        titles = [item.task.title for item in window.today_page._items + window.todo_page._items]
        assert "窗口冒烟测试" in titles
        assert window.stack.count() == 6
        window.set_page("tools")
        assert not window.nav._page_icon("nav_tools").isNull()
        assert window.tools_page._current == "json"
        assert window.tools_page.stack.count() == 7
        window.tools_page._set_tool("alias")
        window.tools_page._set_tool("almanac")
        assert "宜" in window.tools_page._almanac_out.toPlainText()
        window.toggle_compact()
        app.processEvents()
        assert window._compact is True
        assert window.chat_page._compact is True
        assert window.height() < 320
        window.toggle_compact()
        app.processEvents()
        assert window._compact is False
        from service.hotkey_service import normalize_hotkey, parse_hotkey, restore_ctrl_letter_key
        from PySide6.QtCore import QByteArray, QEvent, Qt
        from PySide6.QtGui import QKeyEvent

        assert parse_hotkey("Ctrl+Alt+T") is not None
        assert parse_hotkey("Ctrl+H") is not None
        assert parse_hotkey("T") is None
        assert normalize_hotkey("ctrl+alt+n", "Ctrl+Alt+N").lower().endswith("n")
        assert restore_ctrl_letter_key(int(Qt.Key_Backspace), Qt.ControlModifier, 0) == int(Qt.Key_H)
        from service.hotkey_service import _event_kind

        assert "windows_generic_MSG" in _event_kind(QByteArray(b"windows_generic_MSG"))
        assert window._hotkey_bindings()["todo"]
        assert window._hotkey_bindings()["hide"] == "Ctrl+Alt+H"
        from ui.hotkey_edit import HotkeyEdit

        editor = HotkeyEdit("Ctrl+Alt+H", window)
        editor._start_listen()
        press = QKeyEvent(QEvent.KeyPress, Qt.Key_Backspace, Qt.ControlModifier)
        editor.keyPressEvent(press)
        assert editor.sequence() == "Ctrl+H"
        editor.deleteLater()
        window.show()
        window.toggle_hidden()
        app.processEvents()
        assert window.isVisible() is False
        window.toggle_hidden()
        app.processEvents()
        assert window.isVisible() is True
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
