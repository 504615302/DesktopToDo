from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, QObject, QPoint, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from model.report import WeeklyReport
from service.ai_service import AIClientError
from service.app_context import AppContext
from service.report_service import week_range, week_title
from ui.datetime_picker import Chip, IconButton
from ui.icons import stroke_icon
from ui.page_utils import make_scroll, style_chip
from ui.styles import Theme

OPTIMIZE = [
    ("优化语言", "优化语言表达，保持事实不变"),
    ("更正式", "使用更正式的工作语言"),
    ("更简洁", "更简洁，删除空话"),
    ("突出成果", "突出实际完成成果与价值"),
    ("技术化", "使用更专业的技术表达"),
]

WEEK_HEADINGS = {
    "this": {"cute": "本周小结 ♪", "business": "本周纪要", "minimal": "本周", "tech": "本周同步"},
    "last": {"cute": "上周小结 ♪", "business": "上周纪要", "minimal": "上周", "tech": "上周同步"},
    "custom": {"cute": "自选一周 ♪", "business": "自选区间", "minimal": "自定义", "tech": "自定义区间"},
}

GENERATE_LABEL = {
    "cute": "帮我写周报",
    "business": "生成周报",
    "minimal": "生成周报",
    "tech": "生成周报",
}

EDITOR_HINT = {
    "cute": "点一下生成，把这周写成周报 ✦",
    "business": "生成后可在此修改，再保存或导出",
    "minimal": "生成结果会显示在这里，可直接修改",
    "tech": "输出将显示在这里，可继续改写",
}

NOTES_HINT = {
    "cute": "还想告诉 AI 的一句（可选）",
    "business": "补充说明（可选）",
    "minimal": "补充内容（可选）",
    "tech": "附加指令（可选）",
}


class _AIWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, runner):
        super().__init__()
        self._runner = runner

    def run(self) -> None:
        try:
            self.finished.emit(self._runner())
        except AIClientError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class ReportPage(QWidget):
    def __init__(self, theme: Theme, ctx: AppContext, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._ctx = ctx
        self._range = "this"
        self._start, self._end = week_range("this")
        self._current: WeeklyReport | None = None
        self._thread: QThread | None = None
        self._worker: _AIWorker | None = None
        self._material_checks: dict[str, list[QCheckBox]] = {"completed": [], "memos": [], "unfinished": []}
        self._materials_open = False

        self.week_hero = QWidget()
        self.week_hero.setObjectName("weekHero")
        self.week_hero.setAttribute(Qt.WA_StyledBackground, True)
        hero = QVBoxLayout(self.week_hero)
        hero.setContentsMargins(14, 12, 10, 12)
        hero.setSpacing(8)

        self.week_title = QLabel()
        self.week_dates = QLabel()
        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(2)
        title_col.addWidget(self.week_title)
        title_col.addWidget(self.week_dates)

        self.history_btn = IconButton("note", theme.accent, "历史周报", 32, 18)
        self.history_btn.set_asset("nav_report")
        self.history_btn.clicked.connect(self._open_history)
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(6)
        title_row.addLayout(title_col, 1)
        title_row.addWidget(self.history_btn, 0, Qt.AlignTop)
        hero.addLayout(title_row)

        range_row = QHBoxLayout()
        range_row.setSpacing(6)
        self._range_buttons: dict[str, Chip] = {}
        for key, label in (("this", "本周"), ("last", "上周"), ("custom", "自选")):
            button = Chip(label, theme)
            button.clicked.connect(lambda _=False, value=key: self._set_range(value))
            range_row.addWidget(button)
            self._range_buttons[key] = button
        range_row.addStretch()
        range_wrap = QWidget()
        range_wrap.setLayout(range_row)
        hero.addWidget(range_wrap)

        custom_row = QHBoxLayout()
        custom_row.setSpacing(6)
        self.start_edit = QDateEdit()
        self.end_edit = QDateEdit()
        for editor in (self.start_edit, self.end_edit):
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("M月d日")
            editor.setFixedHeight(32)
            editor.dateChanged.connect(self._on_custom_date)
        self._date_sep = QLabel("—")
        custom_row.addWidget(self.start_edit, 1)
        custom_row.addWidget(self._date_sep)
        custom_row.addWidget(self.end_edit, 1)
        self.custom_wrap = QWidget()
        self.custom_wrap.setLayout(custom_row)
        self.custom_wrap.hide()
        hero.addWidget(self.custom_wrap)

        source_row = QHBoxLayout()
        source_row.setContentsMargins(2, 0, 2, 0)
        source_row.setSpacing(6)
        self._source_buttons: dict[str, QPushButton] = {}
        for key, label in (("completed", "完成"), ("memos", "备忘"), ("unfinished", "未完")):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setChecked(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(28)
            button.clicked.connect(self._on_source_toggled)
            source_row.addWidget(button)
            self._source_buttons[key] = button
        source_row.addStretch()
        self.materials_toggle = IconButton("chevron-down", theme.text_secondary, "展开素材，可单独勾选", 28, 14)
        self.materials_toggle.clicked.connect(self._toggle_materials)
        source_row.addWidget(self.materials_toggle)
        source_wrap = QWidget()
        source_wrap.setLayout(source_row)
        hero.addWidget(source_wrap)

        self.src_completed = self._source_buttons["completed"]
        self.src_memos = self._source_buttons["memos"]
        self.src_unfinished = self._source_buttons["unfinished"]

        self.materials = QWidget()
        self.materials_layout = QVBoxLayout(self.materials)
        self.materials_layout.setContentsMargins(0, 0, 4, 0)
        self.materials_layout.setSpacing(2)
        self.materials_scroll = make_scroll(self.materials)
        self.materials_scroll.setMaximumHeight(120)
        self.materials_scroll.setMinimumHeight(64)
        self.materials_scroll.hide()
        hero.addWidget(self.materials_scroll)

        combo_row = QHBoxLayout()
        combo_row.setSpacing(8)
        self.model_combo = QComboBox()
        self.template_combo = QComboBox()
        self.model_combo.setMinimumHeight(34)
        self.template_combo.setMinimumHeight(34)
        self.model_combo.setToolTip("AI 模型")
        self.template_combo.setToolTip("周报模板")
        combo_row.addWidget(self.model_combo, 1)
        combo_row.addWidget(self.template_combo, 1)

        self.notes = QLineEdit()
        self.notes.setFixedHeight(34)

        self.generate_btn = QPushButton()
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.setFixedHeight(38)
        self.generate_btn.clicked.connect(self.generate)

        self.editor_card = QWidget()
        self.editor_card.setObjectName("reportEditor")
        self.editor_card.setAttribute(Qt.WA_StyledBackground, True)
        editor_box = QVBoxLayout(self.editor_card)
        editor_box.setContentsMargins(12, 10, 12, 10)
        editor_box.setSpacing(8)

        self.status = QLabel()
        self.status.hide()
        self.editor = QPlainTextEdit()
        self.editor.setFrameStyle(QPlainTextEdit.NoFrame)
        self.editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.editor.setMinimumHeight(88)

        self.optimize_btn = QPushButton("润色")
        self.optimize_btn.setCursor(Qt.PointingHandCursor)
        self.optimize_btn.setFixedHeight(30)
        opt_menu = QMenu(self.optimize_btn)
        for label, instruction in OPTIMIZE:
            opt_menu.addAction(label, lambda inst=instruction: self.optimize(inst))
        opt_menu.addSeparator()
        opt_menu.addAction("重新生成", self.generate)
        self.optimize_btn.setMenu(opt_menu)

        self.save_btn = QPushButton("保存")
        self.copy_btn = QPushButton("复制")
        self.export_btn = QPushButton("导出")
        for button in (self.save_btn, self.copy_btn, self.export_btn):
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(30)
        self.save_btn.clicked.connect(self.save_report)
        self.copy_btn.clicked.connect(self.copy_report)
        self.export_btn.clicked.connect(self.export_markdown)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(6)
        action_row.addWidget(self.optimize_btn)
        action_row.addStretch()
        action_row.addWidget(self.save_btn)
        action_row.addWidget(self.copy_btn)
        action_row.addWidget(self.export_btn)

        editor_box.addWidget(self.status)
        editor_box.addWidget(self.editor, 1)
        editor_box.addLayout(action_row)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        root.addWidget(self.week_hero)
        root.addLayout(combo_row)
        root.addWidget(self.notes)
        root.addWidget(self.generate_btn)
        root.addWidget(self.editor_card, 1)

        self._apply_styles()
        self.reload_options()
        self._set_range("this")

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._apply_styles()
        self._refresh_range_buttons()
        self._refresh_source_chips()
        self._refresh_range_label()
        self._refresh_materials()

    def _apply_styles(self) -> None:
        theme = self._theme
        radius = max(12, theme.chip_radius)
        self.week_title.setStyleSheet(
            f"color: {theme.accent}; font-size: 20px; font-weight: 700; letter-spacing: 0.4px;"
        )
        self.week_dates.setStyleSheet(f"color: {theme.text_secondary}; font-size: 12px;")
        self._date_sep.setStyleSheet(f"color: {theme.text_muted};")
        self.status.setStyleSheet(f"color: {theme.text_muted}; font-size: 11px;")
        self.history_btn.set_asset("nav_report")
        self.materials_toggle.set_color(theme.text_secondary)
        self.generate_btn.setText(GENERATE_LABEL.get(theme.name, "生成周报"))
        self.generate_btn.setIcon(stroke_icon("sparkle", theme.primary_text, 16))
        self.editor.setPlaceholderText(EDITOR_HINT.get(theme.name, EDITOR_HINT["minimal"]))
        self.notes.setPlaceholderText(NOTES_HINT.get(theme.name, NOTES_HINT["minimal"]))
        self.week_hero.setStyleSheet(
            f"""
            QWidget#weekHero {{
                background: {theme.accent_soft};
                border: 1px solid {theme.border};
                border-radius: {radius}px;
            }}
            """
        )
        self.editor_card.setStyleSheet(
            f"""
            QWidget#reportEditor {{
                background: {theme.surface};
                border: 1px solid {theme.border};
                border-radius: {radius}px;
            }}
            QWidget#reportEditor QPlainTextEdit {{
                background: transparent;
                border: none;
                padding: 0;
            }}
            QWidget#reportEditor QPlainTextEdit:focus {{
                border: none;
            }}
            """
        )
        ghost = f"""
            QPushButton {{
                background: {theme.surface};
                color: {theme.text_secondary};
                border: 1px solid {theme.border};
                border-radius: {theme.chip_radius}px;
                padding: 4px 10px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {theme.hover};
                color: {theme.text};
            }}
            QPushButton::menu-indicator {{
                width: 10px;
            }}
        """
        for button in (self.optimize_btn, self.save_btn, self.copy_btn, self.export_btn):
            button.setStyleSheet(ghost)
        for button in self._range_buttons.values():
            button.apply_theme(theme)
        self._refresh_source_chips()

    def reload_options(self) -> None:
        settings = self._ctx.settings.settings
        self.model_combo.blockSignals(True)
        self.template_combo.blockSignals(True)
        self.model_combo.clear()
        for config in self._ctx.reports.models():
            self.model_combo.addItem(config.name, config.id)
            if settings.default_ai_model == config.id:
                self.model_combo.setCurrentIndex(self.model_combo.count() - 1)
        self.template_combo.clear()
        for template in self._ctx.reports.templates():
            name = template.name + ("（默认）" if template.is_default else "")
            self.template_combo.addItem(name, template.id)
            if settings.default_report_template == template.id or (
                template.is_default and settings.default_report_template is None
            ):
                self.template_combo.setCurrentIndex(self.template_combo.count() - 1)
        self.model_combo.blockSignals(False)
        self.template_combo.blockSignals(False)
        self._refresh_materials()

    def _set_range(self, kind: str) -> None:
        self._range = kind
        if kind != "custom":
            self._start, self._end = week_range(kind)
            self.start_edit.setDate(QDate(self._start.year, self._start.month, self._start.day))
            self.end_edit.setDate(QDate(self._end.year, self._end.month, self._end.day))
        self.custom_wrap.setVisible(kind == "custom")
        self._refresh_range_buttons()
        self._refresh_range_label()
        self._refresh_materials()

    def _on_custom_date(self) -> None:
        if self._range != "custom":
            return
        start = self._qdate(self.start_edit.date())
        end = self._qdate(self.end_edit.date())
        self._start, self._end = (start, end) if start <= end else (end, start)
        self._refresh_range_label()
        self._refresh_materials()

    def _qdate(self, value: QDate) -> date:
        return date(value.year(), value.month(), value.day())

    def _refresh_range_buttons(self) -> None:
        for key, button in self._range_buttons.items():
            button.setChecked(key == self._range)

    def _refresh_range_label(self) -> None:
        names = WEEK_HEADINGS.get(self._range, WEEK_HEADINGS["this"])
        self.week_title.setText(names.get(self._theme.name, names["minimal"]))
        if self._start.month == self._end.month:
            span = f"{self._start.month}月{self._start.day}日 — {self._end.day}日"
        else:
            span = f"{self._start.month}月{self._start.day}日 — {self._end.month}月{self._end.day}日"
        self.week_dates.setText(span)

    def _on_source_toggled(self) -> None:
        self._refresh_source_chips()
        self._refresh_materials()

    def _toggle_materials(self) -> None:
        self._materials_open = not self._materials_open
        self.materials_scroll.setVisible(self._materials_open)
        kind = "chevron-up" if self._materials_open else "chevron-down"
        tip = "收起素材" if self._materials_open else "展开素材，可单独勾选"
        self.materials_toggle.set_kind(kind, self._theme.text_secondary)
        self.materials_toggle.setToolTip(tip)

    def _refresh_source_chips(self) -> None:
        for button in self._source_buttons.values():
            style_chip(button, self._theme, button.isChecked())

    def _refresh_materials(self) -> None:
        while self.materials_layout.count():
            item = self.materials_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        data = self._ctx.reports.collect_materials(
            self._ctx.tasks.list_tasks(),
            self._ctx.memos.list_memos(),
            self._start,
            self._end,
        )
        self._source_buttons["completed"].setText(f"完成 {len(data['completed'])}")
        self._source_buttons["memos"].setText(f"备忘 {len(data['memos'])}")
        self._source_buttons["unfinished"].setText(f"未完 {len(data['unfinished'])}")
        self._refresh_source_chips()
        self._material_checks = {"completed": [], "memos": [], "unfinished": []}
        groups = (
            ("completed", "完成", self.src_completed.isChecked()),
            ("memos", "备忘", self.src_memos.isChecked()),
            ("unfinished", "未完", self.src_unfinished.isChecked()),
        )
        empty = True
        for key, title, enabled in groups:
            if not enabled:
                continue
            items = data[key]
            if not items:
                continue
            empty = False
            heading = QLabel(f"{title}  {len(items)}")
            heading.setStyleSheet(f"color: {self._theme.text_muted}; font-size: 11px; font-weight: 600; padding: 4px 2px 2px 2px;")
            self.materials_layout.addWidget(heading)
            for item in items:
                text = item.display_title() if key == "memos" else item.title
                box = QCheckBox(text)
                box.setChecked(True)
                box.setToolTip(text)
                box.setProperty("payload", item)
                box.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
                self.materials_layout.addWidget(box)
                self._material_checks[key].append(box)
        if empty:
            hint = QLabel("这段时间还没有可勾选的素材")
            hint.setStyleSheet(f"color: {self._theme.text_muted}; padding: 8px 2px;")
            hint.setWordWrap(True)
            self.materials_layout.addWidget(hint)
        self.materials_layout.addStretch()

    def _checked(self, key: str):
        return [box.property("payload") for box in self._material_checks[key] if box.isChecked()]

    def _selected_model(self):
        model_id = self.model_combo.currentData()
        return next((item for item in self._ctx.reports.models() if item.id == model_id), None)

    def _selected_template(self):
        template_id = self.template_combo.currentData()
        return next((item for item in self._ctx.reports.templates() if item.id == template_id), None)

    def generate(self) -> None:
        config = self._selected_model()
        template = self._selected_template()
        if config is None:
            QMessageBox.information(self, "提示", "请先在设置中配置 AI 模型")
            return
        if template is None:
            QMessageBox.information(self, "提示", "请先选择周报模板")
            return
        prompt = self._ctx.reports.build_prompt(
            template,
            self._start,
            self._end,
            self._checked("completed"),
            self._checked("unfinished"),
            self._checked("memos"),
            self.notes.text(),
        )
        self._run_ai(lambda: self._ctx.ai.generate_report(config, prompt), "正在生成周报…")

    def optimize(self, instruction: str) -> None:
        config = self._selected_model()
        content = self.editor.toPlainText().strip()
        if config is None:
            QMessageBox.information(self, "提示", "请先配置 AI 模型")
            return
        if not content:
            QMessageBox.information(self, "提示", "还没有可优化的周报")
            return
        self._run_ai(lambda: self._ctx.ai.optimize(config, content, instruction), "正在优化…")

    def _set_status(self, text: str) -> None:
        self.status.setText(text)
        self.status.setVisible(bool(text))

    def _set_busy(self, busy: bool) -> None:
        self.generate_btn.setEnabled(not busy)
        self.optimize_btn.setEnabled(not busy)

    def _run_ai(self, runner, status: str) -> None:
        if self._thread and self._thread.isRunning():
            return
        self._set_status(status)
        self._set_busy(True)
        thread = QThread(self)
        worker = _AIWorker(runner)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_ai_done)
        worker.failed.connect(self._on_ai_fail)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(lambda: self._set_busy(False))
        self._thread = thread
        self._worker = worker
        thread.start()

    def _on_ai_done(self, text: str) -> None:
        self.editor.setPlainText(text)
        self._set_status("生成完成，可直接改，或点润色")
        self._current = None

    def _on_ai_fail(self, message: str) -> None:
        self._set_status("生成失败")
        QMessageBox.warning(self, "AI 调用失败", message)

    def save_report(self) -> None:
        content = self.editor.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "提示", "周报内容为空")
            return
        report = self._current or WeeklyReport(content=content)
        report.content = content
        report.title = week_title(self._start, self._end)
        report.start_date = self._start
        report.end_date = self._end
        report.template_id = self.template_combo.currentData()
        report.model_config_id = self.model_combo.currentData()
        self._current = self._ctx.reports.save_report(report)
        self._set_status("已保存")

    def copy_report(self) -> None:
        text = self.editor.toPlainText()
        QApplication.clipboard().setText(text)
        self._set_status("已复制到剪贴板")

    def export_markdown(self) -> None:
        content = self.editor.toPlainText().strip()
        if not content:
            return
        title = week_title(self._start, self._end)
        path, _ = QFileDialog.getSaveFileName(self, "导出 Markdown", f"{title}.md", "Markdown (*.md)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        self._set_status("已导出")

    def _open_history(self) -> None:
        menu = QMenu(self)
        reports = self._ctx.reports.reports()
        if not reports:
            empty = menu.addAction("还没有保存过周报")
            empty.setEnabled(False)
        else:
            for report in reports:
                menu.addAction(report.title or "未命名周报", lambda _=False, item=report: self._load_report(item))
        menu.exec(self.history_btn.mapToGlobal(QPoint(0, self.history_btn.height())))

    def _load_report(self, report: WeeklyReport) -> None:
        self._current = report
        self.editor.setPlainText(report.content)
        if report.start_date and report.end_date:
            self._range = "custom"
            self._start, self._end = report.start_date, report.end_date
            self.start_edit.setDate(QDate(self._start.year, self._start.month, self._start.day))
            self.end_edit.setDate(QDate(self._end.year, self._end.month, self._end.day))
            self.custom_wrap.show()
            self._refresh_range_buttons()
            self._refresh_range_label()
            self._refresh_materials()
        self._set_status("已载入历史周报")
