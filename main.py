from __future__ import annotations

import sys

from PySide6.QtCore import QByteArray, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from app_paths import db_path, settings_path
from database.db import Database
from database.memo_repository import MemoRepository
from database.report_repository import ReportRepository
from database.task_repository import TaskRepository
from service.ai_service import AIService
from service.app_context import AppContext
from service.credential_service import CredentialService
from service.memo_service import MemoService
from service.report_service import ReportService
from service.settings_service import SettingsService
from service.startup_service import StartupService
from service.task_service import TaskService
from ui.icons import app_icon
from ui.main_window import MainWindow
from ui.styles import build_stylesheet, resolve_theme
from version import APP_DISPLAY_NAME, APP_ID

APP_NAME = APP_ID
INSTANCE_KEY = "DesktopTODO_SingleInstance"


def _activate_existing() -> bool:
    socket = QLocalSocket()
    socket.connectToServer(INSTANCE_KEY)
    if socket.waitForConnected(150):
        socket.write(QByteArray(b"show"))
        socket.waitForBytesWritten(150)
        socket.disconnectFromServer()
        return True
    return False


def _listen_for_activation(window: MainWindow) -> QLocalServer:
    QLocalServer.removeServer(INSTANCE_KEY)
    server = QLocalServer(window)
    server.newConnection.connect(lambda: _on_second_instance(server, window))
    server.listen(INSTANCE_KEY)
    return server


def _on_second_instance(server: QLocalServer, window: MainWindow) -> None:
    connection = server.nextPendingConnection()
    if connection is None:
        return
    connection.readyRead.connect(window.show_from_tray)
    QTimer.singleShot(50, window.show_from_tray)


def build_context(database: Database, settings_path_value) -> AppContext:
    connection = database.connection()
    credentials = CredentialService()
    ai = AIService(credentials)
    return AppContext(
        tasks=TaskService(TaskRepository(connection)),
        memos=MemoService(MemoRepository(connection)),
        reports=ReportService(ReportRepository(connection), ai, credentials),
        ai=ai,
        credentials=credentials,
        settings=SettingsService(settings_path_value),
        startup=StartupService(),
    )


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_ID)
    app.setApplicationDisplayName(APP_DISPLAY_NAME)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(app_icon())

    if _activate_existing():
        return 0

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, APP_DISPLAY_NAME, "当前系统不支持托盘图标，程序无法常驻运行。")
        return 1

    database = Database(db_path())
    ctx = build_context(database, settings_path())
    if ctx.settings.settings.auto_start != ctx.startup.is_enabled():
        ctx.startup.set_enabled(ctx.settings.settings.auto_start)

    theme = resolve_theme(ctx.settings.settings.theme)
    app.setStyleSheet(build_stylesheet(theme))

    window = MainWindow(ctx)
    _listen_for_activation(window)

    code = app.exec()
    database.close()
    return code


if __name__ == "__main__":
    sys.exit(main())
