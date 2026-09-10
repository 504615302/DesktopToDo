from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from model.settings import AppSettings
from model.task import Priority, Task
from service.settings_service import SettingsService
from service.startup_service import StartupService
from service.task_service import TaskService
from ui.card_window import MARGIN, CardWindow
from ui.settings_dialog import SettingsDialog
from ui.styles import Theme, build_stylesheet, resolve_theme
from ui.task_dialog import TaskDialog
from ui.task_item import TaskItem
from ui.title_bar import TitleBar
from ui.icons import app_icon


FILTERS = [
    ("incomplete", "未完成"),
    ("all", "全部"),
    ("completed", "已完成"),
]


class MainWindow(CardWindow):
    def __init__(
        self,
        task_service: TaskService,
        settings_service: SettingsService,
        startup_service: StartupService,
    ):
        self.task_service = task_service
        self.settings_service = settings_service
        self.startup_service = startup_service
        self.settings: AppSettings = settings_service.settings
        self.theme: Theme = resolve_theme(self.settings.theme)
        self._really_quit = False
        self._items: list[TaskItem] = []
        super().__init__(self.theme, resizable=True)
        self.setWindowTitle("Desktop TODO")
        self.setWindowIcon(app_icon())
        self._build_ui()
        self._setup_tray()
        self._setup_shortcuts()
        self.apply_appearance(show=False, reload=False)
        self._restore_geometry()
        self.reload_tasks()
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self._persist_geometry)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(MARGIN + 14, MARGIN + 8, MARGIN + 14, MARGIN + 12)
        root.setSpacing(8)

        self.title_bar = TitleBar(self.theme)
        self.title_bar.set_date(datetime.now().strftime("%m-%d"))
        self.title_bar.set_pinned(self.settings.always_on_top)
        self.title_bar.settings_clicked.connect(self.open_settings)
        self.title_bar.pin_clicked.connect(self.toggle_pin)
        self.title_bar.minimize_clicked.connect(self.hide)
        self.title_bar.close_clicked.connect(self.hide)
        root.addWidget(self.title_bar)

        self.filter_bar = QWidget()
        filter_layout = QHBoxLayout(self.filter_bar)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(6)
        self._filter_buttons: dict[str, QPushButton] = {}
        for key, label in FILTERS:
            button = QPushButton(label)
            button.setCursor(Qt.PointingHandCursor)
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, value=key: self.set_filter(value))
            filter_layout.addWidget(button)
            self._filter_buttons[key] = button
        filter_layout.addStretch()
        root.addWidget(self.filter_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.viewport().setAutoFillBackground(False)
        self.list_host = QWidget()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(0, 0, 4, 0)
        self.list_layout.setSpacing(2)
        self.list_layout.addStretch()
        self.scroll.setWidget(self.list_host)
        root.addWidget(self.scroll, 1)

        self.quick_add = QLineEdit()
        self.quick_add.setPlaceholderText("＋  添加任务，按 Enter 保存")
        self.quick_add.setFixedHeight(38)
        self.quick_add.returnPressed.connect(self._on_quick_add)
        root.addWidget(self.quick_add)
        self._refresh_filter_buttons()

    def _setup_tray(self) -> None:
        self.tray = QSystemTrayIcon(app_icon(), self)
        self.tray.setToolTip("Desktop TODO")
        menu = QMenu()
        open_action = QAction("打开 TODO", self)
        add_action = QAction("添加任务", self)
        today_action = QAction("查看今日任务", self)
        settings_action = QAction("设置", self)
        quit_action = QAction("退出", self)
        open_action.triggered.connect(self.show_from_tray)
        add_action.triggered.connect(self.quick_add_from_tray)
        today_action.triggered.connect(self.show_today)
        settings_action.triggered.connect(self.open_settings)
        quit_action.triggered.connect(self.quit_app)
        for action in (open_action, add_action, today_action, settings_action):
            menu.addAction(action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.quick_add.setFocus)
        QShortcut(QKeySequence("Esc"), self, activated=self.quick_add.clear)

    def apply_appearance(self, show: bool = True, reload: bool = True) -> None:
        self.theme = resolve_theme(self.settings.theme)
        self.set_theme(self.theme)
        QApplication.instance().setStyleSheet(build_stylesheet(self.theme))
        self.setWindowOpacity(self.settings.opacity)
        self.title_bar.apply_theme(self.theme)
        self.title_bar.set_pinned(self.settings.always_on_top)
        self._refresh_filter_buttons()
        flags = self.windowFlags()
        want_top = Qt.WindowStaysOnTopHint
        has_top = bool(flags & want_top)
        if has_top != self.settings.always_on_top:
            self.apply_flags(self.settings.always_on_top)
        elif show:
            self.show()
        if reload:
            self.reload_tasks()

    def _refresh_filter_buttons(self) -> None:
        for key, button in self._filter_buttons.items():
            active = key == self.settings.filter_mode
            bg = self.theme.chip_active if active else self.theme.surface
            color = self.theme.accent if active else self.theme.text_secondary
            button.setChecked(active)
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background: {bg};
                    color: {color};
                    border: 1px solid {self.theme.border};
                    border-radius: 12px;
                    padding: 4px 10px;
                    font-size: 12px;
                }}
                """
            )

    def set_filter(self, mode: str) -> None:
        self.settings_service.update(filter_mode=mode)
        self.settings = self.settings_service.settings
        self._refresh_filter_buttons()
        self.reload_tasks()

    def toggle_pin(self) -> None:
        self.settings_service.update(always_on_top=not self.settings.always_on_top)
        self.settings = self.settings_service.settings
        self.apply_appearance(reload=False)

    def reload_tasks(self) -> None:
        tasks = self.task_service.list_tasks()
        mode = self.settings.filter_mode
        pending = [task for task in tasks if not task.is_completed]
        completed = [task for task in tasks if task.is_completed]

        visible_pending = pending if mode in {"incomplete", "all"} else []
        visible_completed = completed if mode in {"completed", "all"} else []
        if mode == "incomplete":
            visible_completed = []

        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._items.clear()

        if not visible_pending and not visible_completed:
            empty = QLabel("暂无待办，在下方输入后按 Enter 添加")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {self.theme.text_muted}; padding: 32px 8px;")
            empty.setWordWrap(True)
            self.list_layout.addWidget(empty)
            self.list_layout.addStretch()
            return

        if visible_pending:
            self.list_layout.addWidget(self._section_label(f"未完成  {len(visible_pending)}"))
            for task in visible_pending:
                self._add_item(task)
        if visible_completed:
            self.list_layout.addWidget(self._section_label(f"已完成  {len(visible_completed)}"))
            for task in visible_completed:
                self._add_item(task)
        self.list_layout.addStretch()

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            f"color: {self.theme.text_muted}; font-size: 12px; font-weight: 600; padding: 8px 8px 4px 8px;"
        )
        return label

    def _add_item(self, task: Task) -> None:
        item = TaskItem(task, self.theme)
        item.toggled.connect(self._on_toggled)
        item.edit_requested.connect(self.edit_task)
        item.delete_requested.connect(self.delete_task)
        self.list_layout.addWidget(item)
        self._items.append(item)

    def _on_quick_add(self) -> None:
        title = self.quick_add.text().strip()
        if not title:
            return
        self.task_service.add_task(title)
        self.quick_add.clear()
        self.reload_tasks()

    def _on_toggled(self, task: Task, checked: bool) -> None:
        self.task_service.set_completed(task, checked)
        self.reload_tasks()

    def edit_task(self, task: Task) -> None:
        dialog = TaskDialog(self.theme, task, self)
        if dialog.exec() != TaskDialog.DialogCode.Accepted:
            return
        title, description, priority = dialog.result_values()
        if not title:
            QMessageBox.information(self, "提示", "任务名称不能为空")
            return
        task.title = title
        task.description = description
        task.priority = priority
        self.task_service.update_task(task)
        self.reload_tasks()

    def delete_task(self, task: Task) -> None:
        if task.priority_enum != Priority.NORMAL:
            result = QMessageBox.question(self, "删除任务", "确认删除该任务？")
            if result != QMessageBox.StandardButton.Yes:
                return
        self.task_service.delete_task(task.id)
        self.reload_tasks()

    def open_settings(self) -> None:
        self.show_from_tray()
        dialog = SettingsDialog(self.theme, self.settings, self)
        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return
        values = dialog.result_values()
        self.startup_service.set_enabled(values["auto_start"])
        self.settings_service.update(**values)
        self.settings = self.settings_service.settings
        self.apply_appearance()

    def show_from_tray(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def show_today(self) -> None:
        self.set_filter("incomplete")
        self.show_from_tray()

    def quick_add_from_tray(self) -> None:
        self.show_from_tray()
        self.quick_add.setFocus()
        self.quick_add.selectAll()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_from_tray()

    def quit_app(self) -> None:
        self._really_quit = True
        self._persist_geometry()
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event) -> None:
        if self._really_quit:
            self._persist_geometry()
            event.accept()
            return
        event.ignore()
        self.hide()

    def moveEvent(self, event) -> None:
        super().moveEvent(event)
        self._save_timer.start()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._save_timer.start()

    def _persist_geometry(self) -> None:
        geo = self.geometry()
        self.settings_service.update(
            window_x=geo.x(),
            window_y=geo.y(),
            window_width=max(300, geo.width() - MARGIN * 2),
            window_height=max(400, geo.height() - MARGIN * 2),
        )
        self.settings = self.settings_service.settings

    def _restore_geometry(self) -> None:
        width = self.settings.window_width + MARGIN * 2
        height = self.settings.window_height + MARGIN * 2
        if self.settings.window_x is None or self.settings.window_y is None:
            screen = QGuiApplication.primaryScreen().availableGeometry()
            x = screen.right() - width - 24
            y = screen.top() + 48
            self.setGeometry(x, y, width, height)
        else:
            self.setGeometry(self.settings.window_x, self.settings.window_y, width, height)
        self.clamp_to_screens()
        self.show()
