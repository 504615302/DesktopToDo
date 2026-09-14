from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QTimer,
    Qt,
)
from PySide6.QtGui import QAction, QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from model.settings import AppSettings
from model.task import Priority, Task
from service.app_context import AppContext
from service.hotkey_service import DEFAULT_HOTKEYS, HotkeyService, normalize_hotkey
from service.reminder_service import ReminderService
from ui.ai_model_dialog import AIModelListDialog
from ui.card_window import MARGIN, CardWindow
from ui.chat_page import ChatPage
from ui.dialogs.quick_input_dialog import QuickInputDialog
from ui.dialogs.work_result_dialog import WorkResultDialog
from ui.icons import app_icon, stroke_icon
from ui.memo_page import MemoPage
from ui.nav_bar import NavBar
from ui.page_utils import style_quick_add
from ui.report_page import ReportPage
from ui.settings_dialog import SettingsDialog
from ui.styles import Theme, build_stylesheet, resolve_theme
from ui.support_dialog import SupportAuthorDialog
from ui.task_dialog import TaskDialog
from ui.template_dialog import TemplateListDialog
from ui.title_bar import TitleBar
from ui.today_page import TodayPage
from ui.todo_page import TodoPage
from ui.tools_page import ToolsPage
from version import APP_DISPLAY_NAME


class MainWindow(CardWindow):
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.task_service = ctx.tasks
        self.settings_service = ctx.settings
        self.startup_service = ctx.startup
        self.settings: AppSettings = ctx.settings.settings
        self.theme: Theme = resolve_theme(self.settings.theme)
        self._really_quit = False
        self._alert_anim: QPropertyAnimation | None = None
        self._alert_origin: QPoint | None = None
        self._hotkeys: HotkeyService | None = None
        self._hotkeys_paused = False
        self._shortcuts: list[QShortcut] = []
        self._fallback_shortcuts: list[QShortcut] = []
        self._compact = False
        self._full_geometry = None
        self._page_before_compact = "today"
        super().__init__(self.theme, resizable=True)
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setWindowIcon(app_icon())
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self._persist_geometry)
        self._build_ui()
        self._setup_tray()
        self._setup_shortcuts()
        self._setup_reminders()
        self.apply_appearance(show=False, reload=False)
        self._restore_geometry()
        self.set_page(self.settings.current_page or "today")
        self.reload_all()
        if self.settings.compact_mode:
            QTimer.singleShot(0, self._enter_compact)
        QTimer.singleShot(400, self._install_hotkeys)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(MARGIN + 14, MARGIN + 8, MARGIN + 14, MARGIN + 10)
        root.setSpacing(6)

        self.title_bar = TitleBar(self.theme)
        self.title_bar.set_date(datetime.now().strftime("%m-%d"))
        self.title_bar.set_locked(self.settings.lock_position)
        self.title_bar.set_pinned(self.settings.always_on_top)
        self.title_bar.settings_clicked.connect(self.open_settings)
        self.title_bar.lock_clicked.connect(self.toggle_lock)
        self.title_bar.pin_clicked.connect(self.toggle_pin)
        self.title_bar.theme_selected.connect(self.set_theme_mode)
        self.title_bar.minimize_clicked.connect(self.hide)
        self.title_bar.compact_clicked.connect(self.toggle_compact)
        self.title_bar.close_clicked.connect(self.hide)
        root.addWidget(self.title_bar)

        self.banner = QLabel()
        self.banner.setWordWrap(True)
        self.banner.setAlignment(Qt.AlignCenter)
        self.banner.hide()
        root.addWidget(self.banner)

        self.nav = NavBar(self.theme)
        self.nav.page_changed.connect(self.set_page)
        root.addWidget(self.nav)

        self.stack = QStackedWidget()
        self.today_page = TodayPage(self.theme)
        self.todo_page = TodoPage(self.theme, self.settings.filter_mode)
        self.memo_page = MemoPage(self.theme, self.ctx.memos)
        self.report_page = ReportPage(self.theme, self.ctx)
        self.chat_page = ChatPage(self.theme, self.ctx)
        self.tools_page = ToolsPage(self.theme, self.ctx)
        for page in (self.today_page, self.todo_page):
            page.task_toggled.connect(self._on_toggled)
            page.edit_requested.connect(self.edit_task)
            page.delete_requested.connect(self.delete_task)
            page.report_toggled.connect(self.toggle_task_report)
            page.result_requested.connect(self.record_result)
        self.today_page.memo_open_requested.connect(self.open_memo)
        self.todo_page.filter_changed.connect(self._on_todo_filter)
        self.memo_page.changed.connect(self._on_memo_changed)
        self.stack.addWidget(self.today_page)
        self.stack.addWidget(self.todo_page)
        self.stack.addWidget(self.memo_page)
        self.stack.addWidget(self.report_page)
        self.stack.addWidget(self.chat_page)
        self.stack.addWidget(self.tools_page)
        root.addWidget(self.stack, 1)
        self.chat_page.layout_changed.connect(self._fit_compact_size)

        add_row = QWidget()
        add_layout = QHBoxLayout(add_row)
        add_layout.setContentsMargins(10, 0, 10, 0)
        add_layout.setSpacing(8)
        self._plus_icon = QLabel()
        self._plus_icon.setFixedSize(18, 18)
        self.quick_add = QLineEdit()
        self.quick_add.setPlaceholderText(self.theme.placeholder)
        self.quick_add.setFixedHeight(40)
        self.quick_add.returnPressed.connect(self._on_quick_add)
        add_layout.addWidget(self._plus_icon)
        add_layout.addWidget(self.quick_add, 1)
        add_row.setObjectName("quickAdd")
        self.quick_add_row = add_row
        root.addWidget(add_row)
        self._style_quick_add()
        self._style_banner()

    def _setup_tray(self) -> None:
        self.tray = QSystemTrayIcon(app_icon(), self)
        self.tray.setToolTip(APP_DISPLAY_NAME)
        menu = QMenu()
        actions = [
            (f"打开{APP_DISPLAY_NAME}", self.show_from_tray),
            ("新增 Todo", self.quick_add_from_tray),
            ("新增备忘录", self.quick_memo_from_tray),
            ("AI 周报", self.open_report),
            ("AI 问答", self.open_chat),
            ("小工具", self.open_tools),
            ("支持作者", self.open_support),
            ("设置", self.open_settings),
        ]
        for text, slot in actions:
            action = QAction(text, self)
            action.triggered.connect(slot)
            menu.addAction(action)
        menu.addSeparator()
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _setup_shortcuts(self) -> None:
        self._apply_local_shortcuts()
        self._apply_hotkey_shortcuts()

    def _hotkey_bindings(self) -> dict[str, str]:
        settings = self.settings
        return {
            "todo": normalize_hotkey(settings.hotkey_todo, DEFAULT_HOTKEYS["todo"]),
            "memo": normalize_hotkey(settings.hotkey_memo, DEFAULT_HOTKEYS["memo"]),
            "report": normalize_hotkey(settings.hotkey_report, DEFAULT_HOTKEYS["report"]),
            "chat": normalize_hotkey(settings.hotkey_chat, DEFAULT_HOTKEYS["chat"]),
            "hide": normalize_hotkey(settings.hotkey_hide, DEFAULT_HOTKEYS["hide"]),
        }

    def _clear_shortcuts(self, items: list[QShortcut]) -> None:
        for item in items:
            item.setParent(None)
            item.deleteLater()

    def _bind_shortcut(self, sequence: str, slot) -> QShortcut:
        shortcut = QShortcut(QKeySequence(sequence), self)
        shortcut.activated.connect(slot)
        return shortcut

    def _apply_local_shortcuts(self) -> None:
        self._clear_shortcuts(self._shortcuts)
        self._shortcuts = [
            self._bind_shortcut("Ctrl+N", self.quick_add.setFocus),
            self._bind_shortcut("Esc", self.quick_add.clear),
        ]

    def _apply_hotkey_shortcuts(self, skip: set[str] | None = None) -> None:
        skip = skip or set()
        self._clear_shortcuts(self._fallback_shortcuts)
        self._fallback_shortcuts = []
        slots = {
            "todo": self.quick_add_from_tray,
            "memo": self.quick_memo_from_tray,
            "report": self.open_report,
            "chat": self.open_chat,
            "hide": self.toggle_hidden,
        }
        for action, sequence in self._hotkey_bindings().items():
            if action in skip:
                continue
            self._fallback_shortcuts.append(self._bind_shortcut(sequence, slots[action]))

    def _apply_shortcuts(self) -> None:
        self._apply_local_shortcuts()
        skip = self._hotkeys.registered_actions() if self._hotkeys else set()
        self._apply_hotkey_shortcuts(skip)

    def _pause_hotkeys(self) -> None:
        self._hotkeys_paused = True
        if self._hotkeys:
            self._hotkeys.uninstall()
        self._clear_shortcuts(self._fallback_shortcuts)
        self._fallback_shortcuts = []

    def _install_hotkeys(self) -> None:
        self._hotkeys_paused = False
        if self._hotkeys is None:
            self._hotkeys = HotkeyService(self)
            self._hotkeys.activated.connect(self._on_hotkey)
        self._hotkeys.install(QApplication.instance(), self._hotkey_bindings())
        self._apply_shortcuts()

    def _on_hotkey(self, action: str) -> None:
        if action == "todo":
            self.quick_add_from_tray()
        elif action == "memo":
            self.quick_memo_from_tray()
        elif action == "report":
            self.open_report()
        elif action == "chat":
            self.open_chat()
        elif action == "hide":
            self.toggle_hidden()

    def _setup_reminders(self) -> None:
        self.reminder_service = ReminderService(self.task_service, self)
        self.ctx.reminders = self.reminder_service
        self.reminder_service.triggered.connect(self.on_reminder)

    def apply_appearance(self, show: bool = True, reload: bool = True) -> None:
        self.settings = self.settings_service.settings
        self.theme = resolve_theme(self.settings.theme)
        self.set_theme(self.theme)
        self.set_locked(self.settings.lock_position)
        QApplication.instance().setStyleSheet(build_stylesheet(self.theme))
        self.setWindowOpacity(self.settings.opacity)
        self.title_bar.apply_theme(self.theme)
        self.title_bar.set_locked(self.settings.lock_position)
        self.title_bar.set_pinned(self.settings.always_on_top)
        self.nav.apply_theme(self.theme)
        self.today_page.apply_theme(self.theme)
        self.todo_page.apply_theme(self.theme)
        self.memo_page.apply_theme(self.theme)
        self.report_page.apply_theme(self.theme)
        self.chat_page.apply_theme(self.theme)
        self.tools_page.apply_theme(self.theme)
        self._style_quick_add()
        self._style_banner()
        self._sync_quick_add_mode()
        self.apply_flags(self.settings.always_on_top)
        if self._hotkeys is not None and not self._hotkeys_paused:
            QTimer.singleShot(0, self._install_hotkeys)
        if self._compact:
            self._apply_compact_chrome()
            QTimer.singleShot(0, self._fit_compact_size)
        if show:
            self.show()
        if reload:
            self.reload_all()

    def _style_quick_add(self) -> None:
        self._plus_icon.setPixmap(stroke_icon("plus", self.theme.accent, 16).pixmap(16, 16))
        style_quick_add(self.quick_add_row, self.theme)

    def _style_banner(self) -> None:
        self.banner.setStyleSheet(
            f"""
            QLabel {{
                background: {self.theme.banner_bg};
                color: {self.theme.banner_text};
                border-radius: {self.theme.chip_radius}px;
                padding: 8px 10px;
                font-weight: 600;
            }}
            """
        )

    def set_page(self, key: str) -> None:
        mapping = {"today": 0, "todo": 1, "memo": 2, "report": 3, "chat": 4, "tools": 5}
        index = mapping.get(key, 0)
        key = list(mapping.keys())[index]
        if self._compact and key != "chat":
            self._exit_compact()
        self.stack.setCurrentIndex(index)
        self.nav.set_page(key)
        self.settings_service.update(current_page=key)
        self.settings = self.settings_service.settings
        self._sync_quick_add_mode()
        if key == "report":
            self.report_page.reload_options()
        elif key == "chat":
            self.chat_page.reload_options()

    def _sync_quick_add_mode(self) -> None:
        if self._compact:
            self.quick_add_row.hide()
            return
        page = self.settings.current_page
        self.quick_add_row.setVisible(page in {"today", "todo"})
        self.quick_add.setPlaceholderText(self.theme.placeholder)

    def toggle_lock(self) -> None:
        self.settings_service.update(lock_position=not self.settings.lock_position)
        self.settings = self.settings_service.settings
        self.apply_appearance(reload=False)

    def toggle_pin(self) -> None:
        self.settings_service.update(always_on_top=not self.settings.always_on_top)
        self.settings = self.settings_service.settings
        self.apply_appearance(reload=False)

    def toggle_compact(self) -> None:
        if self._compact:
            self._exit_compact()
        else:
            self._enter_compact()

    def _enter_compact(self) -> None:
        if self._compact:
            return
        self._full_geometry = self.geometry()
        self._page_before_compact = self.settings.current_page or "today"
        self._compact = True
        self._apply_compact_chrome()
        self.chat_page.reload_options()
        self.chat_page.set_compact(True)
        self.settings_service.update(compact_mode=True)
        self.settings = self.settings_service.settings
        self.show_from_tray()
        QTimer.singleShot(0, self._fit_compact_size)

    def _exit_compact(self) -> None:
        if not self._compact:
            return
        self._compact = False
        self.chat_page.set_compact(False)
        self.set_compact_limits(False)
        self.title_bar.set_compact(False)
        self.nav.show()
        self._sync_stack_size_policy()
        self.settings_service.update(compact_mode=False)
        self.settings = self.settings_service.settings
        self.set_page(self._page_before_compact or "today")
        if self._full_geometry is not None:
            self.setGeometry(self._full_geometry)
        self.clamp_to_screens()

    def _apply_compact_chrome(self) -> None:
        self.set_compact_limits(True)
        self.title_bar.set_compact(True)
        self.nav.hide()
        self.banner.hide()
        self.quick_add_row.hide()
        self.stack.setCurrentIndex(4)
        self._sync_stack_size_policy()

    def _sync_stack_size_policy(self) -> None:
        for index in range(self.stack.count()):
            page = self.stack.widget(index)
            if self._compact:
                expanding = page is self.chat_page
                vertical = QSizePolicy.Minimum if expanding else QSizePolicy.Ignored
                page.setSizePolicy(QSizePolicy.Expanding if expanding else QSizePolicy.Ignored, vertical)
            else:
                page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stack.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum if self._compact else QSizePolicy.Expanding,
        )
        self.stack.setMinimumHeight(0)

    def _fit_compact_size(self) -> None:
        if not self._compact:
            return
        margins = self.layout().contentsMargins()
        spacing = self.layout().spacing()
        needed = (
            margins.top()
            + margins.bottom()
            + self.title_bar.height()
            + spacing
            + self.chat_page.compact_height()
        )
        min_h = margins.top() + margins.bottom() + self.title_bar.height() + spacing + 36
        max_h = min_h + spacing + 280 + 24
        height = min(max(int(needed), int(min_h)), int(max_h))
        geo = self.geometry()
        if abs(geo.height() - height) < 2:
            return
        screen = QGuiApplication.screenAt(geo.center())
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        y = geo.y()
        if y + height > avail.bottom():
            y = max(avail.top(), avail.bottom() - height)
        self.setGeometry(geo.x(), y, geo.width(), height)

    def set_theme_mode(self, name: str) -> None:
        self.settings_service.update(theme=name)
        self.settings = self.settings_service.settings
        self.apply_appearance()

    def reload_all(self) -> None:
        tasks = self.task_service.list_tasks()
        memos = self.ctx.memos.list_memos()
        self.today_page.reload(tasks, memos)
        self.todo_page.reload(tasks)
        self.memo_page.reload()
        self.report_page.reload_options()
        self.chat_page.reload_options()

    def _on_todo_filter(self, mode: str) -> None:
        self.settings_service.update(filter_mode=mode)
        self.settings = self.settings_service.settings
        self.todo_page.reload(self.task_service.list_tasks())

    def _on_memo_changed(self) -> None:
        self.today_page.reload(self.task_service.list_tasks(), self.ctx.memos.list_memos())
        self.report_page.reload_options()
        self.chat_page.reload_options()

    def _on_quick_add(self) -> None:
        text = self.quick_add.text().strip()
        if not text:
            return
        if self.settings.current_page == "memo":
            self.ctx.memos.add_memo(text)
            self.memo_page.reload()
        else:
            self.task_service.add_task(text)
        self.quick_add.clear()
        self.reload_all()

    def _on_toggled(self, task: Task, checked: bool) -> None:
        self.task_service.set_completed(task, checked)
        self.reload_all()

    def edit_task(self, task: Task) -> None:
        dialog = TaskDialog(self.theme, task, self)
        if dialog.exec() != TaskDialog.DialogCode.Accepted:
            return
        values = dialog.result_values()
        if not values["title"]:
            QMessageBox.information(self, "提示", "任务名称不能为空")
            return
        task.title = values["title"]
        task.description = values["description"]
        task.priority = values["priority"]
        task.due_time = values["due_time"]
        task.reminder_minutes = values["reminder_minutes"]
        task.category = values["category"]
        task.include_in_report = values["include_in_report"]
        task.reminded_at = None
        self.task_service.update_task(task)
        self.reload_all()

    def delete_task(self, task: Task) -> None:
        if task.priority_enum in {Priority.HIGH, Priority.URGENT}:
            result = QMessageBox.question(self, "删除任务", "确认删除该任务？")
            if result != QMessageBox.StandardButton.Yes:
                return
        self.task_service.delete_task(task.id)
        self.reload_all()

    def toggle_task_report(self, task: Task) -> None:
        task.include_in_report = not task.include_in_report
        self.task_service.update_task(task)
        self.reload_all()

    def record_result(self, task: Task) -> None:
        dialog = WorkResultDialog(self.theme, task, self)
        if dialog.exec() != WorkResultDialog.DialogCode.Accepted:
            return
        content, include = dialog.result_values()
        if not content:
            return
        self.ctx.memos.add_memo(
            content,
            title=f"{task.title} · 工作结果",
            include_in_report=include,
            task_id=task.id,
        )
        if include and not task.include_in_report:
            task.include_in_report = True
            self.task_service.update_task(task)
        self.reload_all()

    def open_memo(self, memo) -> None:
        self.set_page("memo")
        self.memo_page.open_memo(memo)
        self.show_from_tray()

    def open_settings(self) -> None:
        self.show_from_tray()
        self._pause_hotkeys()
        snapshot = self.settings.to_dict()
        dialog = SettingsDialog(self.theme, self.settings, self)
        dialog.opacity_previewed.connect(self.setWindowOpacity)
        dialog.theme_previewed.connect(lambda name: self._preview_theme(name))
        dialog.ai_btn.clicked.connect(lambda: self._open_models(dialog))
        dialog.template_btn.clicked.connect(lambda: self._open_templates(dialog))
        dialog.support_btn.clicked.connect(lambda: self.open_support(dialog))
        accepted = dialog.exec() == SettingsDialog.DialogCode.Accepted
        if not accepted:
            self.settings = AppSettings.from_dict(snapshot)
            self.settings_service.save(self.settings)
            self.apply_appearance()
            self._install_hotkeys()
            return
        values = dialog.result_values()
        self.startup_service.set_enabled(values["auto_start"])
        self.settings_service.update(**values)
        self.settings = self.settings_service.settings
        self.apply_appearance()
        self._install_hotkeys()
        self.report_page.reload_options()
        self.chat_page.reload_options()

    def _open_models(self, parent) -> None:
        AIModelListDialog(self.theme, self.ctx.reports, parent).exec()
        self.report_page.reload_options()
        self.chat_page.reload_options()

    def _open_templates(self, parent) -> None:
        TemplateListDialog(self.theme, self.ctx.reports, parent).exec()
        self.report_page.reload_options()

    def open_support(self, parent=None) -> None:
        host = parent if isinstance(parent, QWidget) else self
        SupportAuthorDialog(self.theme, host).exec()

    def _preview_theme(self, name: str) -> None:
        self.settings.theme = name
        self.apply_appearance()

    def on_reminder(self, task: Task) -> None:
        self.show_from_tray()
        self.set_page("todo")
        self.banner.setText(task.reminder_message())
        self.banner.show()
        QTimer.singleShot(6000, self.banner.hide)
        self.tray.showMessage(APP_DISPLAY_NAME, task.reminder_message(), QSystemTrayIcon.MessageIcon.Information, 5000)
        self.reload_all()
        self.play_reminder_animation(task)

    def play_reminder_animation(self, task: Task) -> None:
        if task.id is not None:
            self.today_page.flash_task(task.id)
            self.todo_page.flash_task(task.id)
        origin = self.pos()
        self._alert_origin = origin
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(720)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        if self.theme.name == "cute":
            anim.setKeyValueAt(0.0, origin)
            anim.setKeyValueAt(0.22, origin + QPoint(0, -22))
            anim.setKeyValueAt(0.42, origin)
            anim.setKeyValueAt(0.62, origin + QPoint(0, -12))
            anim.setKeyValueAt(1.0, origin)
        elif self.theme.name == "business":
            anim.setKeyValueAt(0.0, origin)
            anim.setKeyValueAt(0.12, origin + QPoint(14, 0))
            anim.setKeyValueAt(0.28, origin + QPoint(-12, 0))
            anim.setKeyValueAt(0.44, origin + QPoint(10, 0))
            anim.setKeyValueAt(0.62, origin + QPoint(-6, 0))
            anim.setKeyValueAt(1.0, origin)
        elif self.theme.name == "tech":
            anim.setKeyValueAt(0.0, origin)
            anim.setKeyValueAt(0.16, origin + QPoint(8, -4))
            anim.setKeyValueAt(0.32, origin + QPoint(-6, 2))
            anim.setKeyValueAt(0.5, origin + QPoint(4, -2))
            anim.setKeyValueAt(0.72, origin)
            anim.setKeyValueAt(1.0, origin)
        else:
            anim.setKeyValueAt(0.0, origin)
            anim.setKeyValueAt(0.2, origin + QPoint(0, -8))
            anim.setKeyValueAt(0.45, origin)
            anim.setKeyValueAt(0.7, origin + QPoint(0, -4))
            anim.setKeyValueAt(1.0, origin)
        anim.finished.connect(lambda: self.move(origin))
        self._alert_anim = anim
        anim.start()
        self._pulse_opacity()

    def _pulse_opacity(self) -> None:
        current = self.windowOpacity()
        peak = 1.0 if current < 0.95 else max(0.35, current - 0.25)
        pulse = QPropertyAnimation(self, b"windowOpacity", self)
        pulse.setDuration(640)
        pulse.setKeyValueAt(0.0, current)
        pulse.setKeyValueAt(0.45, peak)
        pulse.setKeyValueAt(1.0, current)
        pulse.start()
        self._opacity_anim = pulse

    def show_from_tray(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def toggle_hidden(self) -> None:
        if self.isVisible():
            self.hide()
            return
        self.show_from_tray()

    def show_today(self) -> None:
        self.set_page("today")
        self.show_from_tray()

    def quick_add_from_tray(self) -> None:
        self.set_page("todo")
        self.show_from_tray()
        self.quick_add.setFocus()
        self.quick_add.selectAll()

    def quick_memo_from_tray(self) -> None:
        self.show_from_tray()
        dialog = QuickInputDialog(self.theme, "快速记录", "输入备忘内容", self)
        if dialog.exec() != QuickInputDialog.DialogCode.Accepted:
            return
        text = dialog.text()
        if not text:
            return
        self.ctx.memos.add_memo(text)
        self.set_page("memo")
        self.reload_all()

    def open_report(self) -> None:
        self.set_page("report")
        self.show_from_tray()

    def open_chat(self) -> None:
        if self._compact:
            self.show_from_tray()
            self.chat_page.focus_input()
            return
        self.set_page("chat")
        self.show_from_tray()

    def open_tools(self) -> None:
        self.set_page("tools")
        self.show_from_tray()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_from_tray()

    def quit_app(self) -> None:
        self._really_quit = True
        self._persist_geometry()
        if self._hotkeys:
            self._hotkeys.uninstall()
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event) -> None:
        if self._really_quit:
            self._persist_geometry()
            if self._hotkeys:
                self._hotkeys.uninstall()
            event.accept()
            return
        event.ignore()
        self.hide()

    def moveEvent(self, event) -> None:
        super().moveEvent(event)
        if self._alert_anim and self._alert_anim.state() == QAbstractAnimation.State.Running:
            return
        if not self.settings.lock_position:
            self._save_timer.start()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if not self.settings.lock_position:
            self._save_timer.start()

    def _persist_geometry(self) -> None:
        geo = self.geometry()
        if self._compact:
            self.settings_service.update(
                window_x=geo.x(),
                window_y=geo.y(),
                compact_mode=True,
            )
            self.settings = self.settings_service.settings
            return
        self.settings_service.update(
            window_x=geo.x(),
            window_y=geo.y(),
            window_width=max(360, geo.width() - MARGIN * 2),
            window_height=max(400, geo.height() - MARGIN * 2),
            compact_mode=False,
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
