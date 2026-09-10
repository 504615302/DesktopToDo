from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from model.report import WeeklyReport
from service.ai_service import AIClientError
from service.app_context import AppContext
from service.report_service import week_range, week_title
from ui.page_utils import make_scroll, style_chip
from ui.styles import Theme

OPTIMIZE = [
    ("优化语言", "优化语言表达，保持事实不变"),
    ("更正式", "使用更正式的工作语言"),
    ("更简洁", "更简洁，删除空话"),
    ("突出成果", "突出实际完成成果与价值"),
    ("技术化", "使用更专业的技术表达"),
]


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

        host = QWidget()
        body = QVBoxLayout(host)
        body.setContentsMargins(0, 0, 8, 0)
        body.setSpacing(8)

        range_row = QHBoxLayout()
        self._range_buttons: dict[str, QPushButton] = {}
        for key, label in (("this", "本周"), ("last", "上周"), ("custom", "自定义")):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _=False, value=key: self._set_range(value))
            range_row.addWidget(button)
            self._range_buttons[key] = button
        range_row.addStretch()
        body.addLayout(range_row)

        self.range_label = QLabel()
        body.addWidget(self.range_label)

        custom_row = QHBoxLayout()
        self.start_edit = QDateEdit()
        self.end_edit = QDateEdit()
        for editor in (self.start_edit, self.end_edit):
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("yyyy-MM-dd")
            editor.dateChanged.connect(self._on_custom_date)
        custom_row.addWidget(self.start_edit)
        custom_row.addWidget(QLabel("~"))
        custom_row.addWidget(self.end_edit)
        self.custom_wrap = QWidget()
        self.custom_wrap.setLayout(custom_row)
        self.custom_wrap.hide()
        body.addWidget(self.custom_wrap)

        self.model_combo = QComboBox()
        self.template_combo = QComboBox()
        body.addWidget(self._caption("模型"))
        body.addWidget(self.model_combo)
        body.addWidget(self._caption("模板"))
        body.addWidget(self.template_combo)

        source_row = QHBoxLayout()
        self.src_completed = QCheckBox("已完成")
        self.src_memos = QCheckBox("备忘录")
        self.src_unfinished = QCheckBox("未完成")
        for box in (self.src_completed, self.src_memos, self.src_unfinished):
            box.setChecked(True)
            box.toggled.connect(self._refresh_materials)
            source_row.addWidget(box)
        source_row.addStretch()
        body.addWidget(self._caption("数据来源"))
        body.addLayout(source_row)

        self.materials = QWidget()
        self.materials_layout = QVBoxLayout(self.materials)
        self.materials_layout.setContentsMargins(0, 0, 0, 0)
        self.materials_layout.setSpacing(4)
        body.addWidget(self._caption("周报素材"))
        body.addWidget(self.materials)

        self.notes = QPlainTextEdit()
        self.notes.setPlaceholderText("补充内容（可选）")
        self.notes.setFixedHeight(64)
        body.addWidget(self.notes)

        self.generate_btn = QPushButton("AI 生成周报")
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.setFixedHeight(36)
        self.generate_btn.clicked.connect(self.generate)
        body.addWidget(self.generate_btn)

        self.status = QLabel()
        body.addWidget(self.status)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("生成结果会显示在这里，可直接修改")
        self.editor.setMinimumHeight(180)
        body.addWidget(self.editor)

        opt_row = QHBoxLayout()
        opt_row.setSpacing(6)
        for label, instruction in OPTIMIZE:
            button = QPushButton(label)
            button.setFixedHeight(28)
            button.clicked.connect(lambda _=False, text=instruction: self.optimize(text))
            opt_row.addWidget(button)
        regen = QPushButton("重新生成")
        regen.setFixedHeight(28)
        regen.clicked.connect(self.generate)
        opt_row.addWidget(regen)
        body.addLayout(opt_row)

        action_row = QHBoxLayout()
        save = QPushButton("保存")
        copy = QPushButton("复制")
        export = QPushButton("导出 Markdown")
        save.clicked.connect(self.save_report)
        copy.clicked.connect(self.copy_report)
        export.clicked.connect(self.export_markdown)
        action_row.addWidget(save)
        action_row.addWidget(copy)
        action_row.addWidget(export)
        body.addLayout(action_row)

        body.addWidget(self._caption("周报历史"))
        self.history = QListWidget()
        self.history.setMaximumHeight(110)
        self.history.itemClicked.connect(self._load_history)
        body.addWidget(self.history)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(make_scroll(host), 1)
        self.reload_options()
        self._set_range("this")

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._refresh_range_buttons()

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
            if settings.default_report_template == template.id or (template.is_default and settings.default_report_template is None):
                self.template_combo.setCurrentIndex(self.template_combo.count() - 1)
        self.model_combo.blockSignals(False)
        self.template_combo.blockSignals(False)
        self._reload_history()
        self._refresh_materials()

    def _caption(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"color: {self._theme.text_secondary}; font-size: 12px; font-weight: 600;")
        return label

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
            style_chip(button, self._theme, key == self._range)

    def _refresh_range_label(self) -> None:
        self.range_label.setText(f"{self._start.strftime('%m-%d')} ~ {self._end.strftime('%m-%d')}")

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
        self._material_checks = {"completed": [], "memos": [], "unfinished": []}
        groups = (
            ("completed", "已完成任务", self.src_completed.isChecked()),
            ("memos", "备忘录", self.src_memos.isChecked()),
            ("unfinished", "未完成任务", self.src_unfinished.isChecked()),
        )
        empty = True
        for key, title, enabled in groups:
            if not enabled:
                continue
            items = data[key]
            if not items:
                continue
            empty = False
            heading = QLabel(title)
            heading.setStyleSheet(f"color: {self._theme.text_muted}; font-size: 11px;")
            self.materials_layout.addWidget(heading)
            for item in items:
                text = item.display_title() if key == "memos" else item.title
                box = QCheckBox(text)
                box.setChecked(True)
                box.setProperty("payload", item)
                self.materials_layout.addWidget(box)
                self._material_checks[key].append(box)
        if empty:
            hint = QLabel("这段时间还没有可勾选的素材")
            hint.setStyleSheet(f"color: {self._theme.text_muted};")
            self.materials_layout.addWidget(hint)

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
            self.notes.toPlainText(),
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

    def _run_ai(self, runner, status: str) -> None:
        if self._thread and self._thread.isRunning():
            return
        self.status.setText(status)
        self.generate_btn.setEnabled(False)
        thread = QThread(self)
        worker = _AIWorker(runner)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_ai_done)
        worker.failed.connect(self._on_ai_fail)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(lambda: self.generate_btn.setEnabled(True))
        self._thread = thread
        self._worker = worker
        thread.start()

    def _on_ai_done(self, text: str) -> None:
        self.editor.setPlainText(text)
        self.status.setText("生成完成，可继续编辑或保存")
        self._current = None

    def _on_ai_fail(self, message: str) -> None:
        self.status.setText("生成失败")
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
        self.status.setText("已保存")
        self._reload_history()

    def copy_report(self) -> None:
        text = self.editor.toPlainText()
        QApplication.clipboard().setText(text)
        self.status.setText("已复制到剪贴板")

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
        self.status.setText("已导出")

    def _reload_history(self) -> None:
        self.history.clear()
        for report in self._ctx.reports.reports():
            item = QListWidgetItem(report.title or "未命名周报")
            item.setData(256, report.id)
            self.history.addItem(item)

    def _load_history(self, item: QListWidgetItem) -> None:
        report_id = item.data(256)
        report = next((row for row in self._ctx.reports.reports() if row.id == report_id), None)
        if report is None:
            return
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
        self.status.setText("已载入历史周报")
