from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtWidgets import QApplication, QSystemTrayIcon

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.db import Database
from database.task_repository import TaskRepository
from service.settings_service import SettingsService
from service.startup_service import StartupService
from service.task_service import TaskService
from ui.main_window import MainWindow
from ui.styles import build_stylesheet, resolve_theme


def test_window_builds() -> None:
    with TemporaryDirectory() as tmp:
        app = QApplication.instance() or QApplication([])
        app.setQuitOnLastWindowClosed(False)
        database = Database(Path(tmp) / "todo.db")
        settings_service = SettingsService(Path(tmp) / "settings.json")
        theme = resolve_theme(settings_service.settings.theme)
        app.setStyleSheet(build_stylesheet(theme))
        window = MainWindow(
            TaskService(TaskRepository(database.connection())),
            settings_service,
            StartupService(),
        )
        assert window.windowTitle() == "Desktop TODO"
        window.task_service.add_task("窗口冒烟测试")
        window.reload_tasks()
        assert any(item.task.title == "窗口冒烟测试" for item in window._items)
        if QSystemTrayIcon.isSystemTrayAvailable():
            assert window.tray.isVisible()
        window._really_quit = True
        window.close()
        database.close()


if __name__ == "__main__":
    test_window_builds()
    print("ui ok")
