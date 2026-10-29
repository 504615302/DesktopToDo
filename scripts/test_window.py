from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtWidgets import QApplication, QPushButton, QSystemTrayIcon

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.db import Database
from main import build_context
from ui.main_window import MainWindow
from ui.entertainment_panel import EntertainmentSettingsDialog
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
        assert window._page_anim.duration() == 160
        assert not window.nav._page_icon("nav_tools").isNull()
        assert window.tools_page._current == "json"
        assert window.tools_page.stack.count() == 8
        window._preview_theme("business")
        assert window._theme_anim.duration() == 180
        assert window.theme.name == "business"
        window.resize(380, 620)
        app.processEvents()
        panel = window.tools_page.entertainment_panel
        buttons = panel.findChildren(QPushButton)
        assert len(buttons) == 3
        assert panel.position_slider.width() >= 80
        assert panel.cinema_button.x() + panel.cinema_button.width() <= panel.width()
        assert panel.settings_button.x() + panel.settings_button.width() <= panel.width()
        long_name = "a-very-long-local-video-file-name-that-should-not-overflow-" + ("wide-" * 40) + ".mp4"
        panel._file_text = long_name
        settings_popup = EntertainmentSettingsDialog(panel._theme, panel, window)
        assert settings_popup.file_label.wordWrap()
        assert settings_popup.file_label.text() == long_name
        settings_popup.volume_slider.setValue(35)
        assert abs(panel.audio_output.volume() - 0.35) < 0.001
        settings_popup.mute_check.setChecked(True)
        assert panel.audio_output.isMuted() is True
        settings_popup.size_slider.setValue(70)
        assert panel._display_scale == 70
        settings_popup.close()
        settings_popup.deleteLater()
        window.tools_page._set_tool("alias")
        window.tools_page._set_tool("almanac")
        assert "宜" in window.tools_page._almanac_out.toPlainText()
        window.tools_page._set_tool("entertainment")
        assert window.tools_page.entertainment_panel.play_button.toolTip() == "播放"
        assert not window.tools_page.entertainment_panel.play_button.icon().isNull()
        window.resize(520, 620)
        app.processEvents()
        stage = window.tools_page.entertainment_panel.video_stage
        small_stage = stage.size()
        small_display = stage.display_geometry().size()
        window.resize(760, 760)
        app.processEvents()
        assert stage.width() > small_stage.width()
        assert stage.height() > small_stage.height()
        assert stage.display_geometry().width() > small_display.width()
        assert stage.display_geometry().height() > small_display.height()
        window.tools_page.entertainment_panel._set_display_scale(70)
        app.processEvents()
        assert stage.display_geometry().width() < stage.width()
        assert window.tools_page.entertainment_panel._display_scale == 70
        normal_stage_height = stage.height()
        window.tools_page.entertainment_panel.set_cinema_mode(True)
        app.processEvents()
        assert window._cinema_mode is True
        assert window.title_bar.isHidden()
        assert window.nav.isHidden()
        assert window.tools_page.chip_bar.isHidden()
        assert stage.height() > normal_stage_height
        assert window.tools_page.entertainment_panel.cinema_button.text() == "退出影音"
        window.tools_page.entertainment_panel.set_cinema_mode(False)
        app.processEvents()
        assert window._cinema_mode is False
        assert window.title_bar.isVisible()
        assert window.nav.isVisible()
        assert window.tools_page.chip_bar.isVisible()
        assert window.tools_page.entertainment_panel.cinema_button.text() == "影音模式"
        window.tools_page.entertainment_panel.set_cinema_mode(True)
        app.processEvents()
        window.tools_page._set_tool("json")
        app.processEvents()
        assert window._cinema_mode is False
        assert window.title_bar.isVisible()
        assert window.nav.isVisible()
        assert window.tools_page.chip_bar.isVisible()
        ctx.settings.update(hover_reveal=True)
        window.settings = ctx.settings.settings
        window._cursor_in_window = lambda: False
        window._apply_window_opacity()
        assert abs(window.windowOpacity() - 0.03) < 0.005
        window._set_hover_reveal_opacity(True)
        assert abs(window.windowOpacity() - window.settings.opacity) < 0.005
        window._set_hover_reveal_opacity(False)
        assert abs(window.windowOpacity() - 0.03) < 0.005
        ctx.settings.update(hover_reveal=False)
        window.settings = ctx.settings.settings
        window._apply_window_opacity()
        assert abs(window.windowOpacity() - window.settings.opacity) < 0.005
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
        from ui.settings_dialog import SettingsDialog

        picker = ChatModelDialog(theme, ctx.reports, None, 0.3, 1024, window)
        assert picker.windowTitle() == "问答模型"
        picker.close()
        settings_dialog = SettingsDialog(window.theme, window.settings, window)
        settings_dialog.hover_reveal_check.setChecked(True)
        assert settings_dialog.result_values()["hover_reveal"] is True
        settings_dialog.close()
        settings_dialog.deleteLater()
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
