from __future__ import annotations

from datetime import date, datetime

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from service.ai_service import AIClientError, NAME_SYSTEM_PROMPT, TRANSLATE_SYSTEM_PROMPT
from service.app_context import AppContext
from service.tools_service import (
    ToolsError,
    almanac_for,
    decode_base64,
    decode_url,
    encode_base64,
    encode_url,
    format_json,
    format_naming,
    hash_md5,
    hash_sha256,
    minify_json,
    naming_styles,
    new_uuid,
    parse_name_words,
    parse_time_value,
    split_identifier,
    time_snapshot,
)
from ui.page_utils import style_chip
from ui.styles import Theme

TOOLS = [
    ("json", "JSON"),
    ("translate", "翻译"),
    ("time", "时间"),
    ("encode", "编码"),
    ("hash", "哈希"),
    ("alias", "别名"),
    ("almanac", "黄历"),
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


class ToolsPage(QWidget):
    def __init__(self, theme: Theme, ctx: AppContext, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._ctx = ctx
        self._current = "json"
        self._thread: QThread | None = None
        self._worker: _AIWorker | None = None
        self._tool_buttons: dict[str, QPushButton] = {}

        chip_row = QGridLayout()
        chip_row.setContentsMargins(0, 0, 0, 0)
        chip_row.setHorizontalSpacing(6)
        chip_row.setVerticalSpacing(6)
        for index, (key, label) in enumerate(TOOLS):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(28)
            button.clicked.connect(lambda _=False, value=key: self._set_tool(value))
            chip_row.addWidget(button, index // 4, index % 4)
            self._tool_buttons[key] = button
        for column in range(4):
            chip_row.setColumnStretch(column, 1)

        self.stack = QStackedWidget()
        self._json_edit = self._text("粘贴 JSON，点格式化或压缩")
        self._zh_edit = self._text("输入要翻译的文本")
        self._en_edit = self._text("译文")
        self._time_edit = QLineEdit()
        self._time_edit.setPlaceholderText("时间或时间戳，例如 2026-09-11 10:32:00")
        self._time_edit.setFixedHeight(34)
        self._time_local = QLineEdit()
        self._time_seconds = QLineEdit()
        self._time_millis = QLineEdit()
        for field in (self._time_local, self._time_seconds, self._time_millis):
            field.setReadOnly(True)
            field.setFixedHeight(32)
        self._codec_in = self._text("原文")
        self._codec_out = self._text("结果")
        self._hash_in = self._text("原文")
        self._hash_out = self._text("结果")
        self._hash_out.setReadOnly(True)
        self._alias_in = self._text("中文含义，或已有英文变量名")
        self._alias_out = self._text("snake / camel / Pascal / CONST / kebab")
        self._alias_out.setReadOnly(True)
        self._almanac_date = QLineEdit()
        self._almanac_date.setPlaceholderText("日期，例如 2026-09-11，空则今天")
        self._almanac_date.setFixedHeight(34)
        self._almanac_out = self._text("宜忌、干支、方位")
        self._almanac_out.setReadOnly(True)
        self._almanac_out.setPlainText(almanac_for(date.today()))

        self.stack.addWidget(
            self._panel(
                self._json_edit,
                [
                    ("格式化", self._format_json),
                    ("压缩", self._minify_json),
                    ("复制", lambda: self._copy(self._json_edit.toPlainText())),
                ],
            )
        )
        self.stack.addWidget(
            self._panel(
                None,
                [
                    ("中 → 英", lambda: self._translate("en")),
                    ("英 → 中", lambda: self._translate("zh")),
                    ("复制译文", lambda: self._copy(self._en_edit.toPlainText())),
                ],
                extra=(self._zh_edit, self._en_edit),
            )
        )
        time_form = QWidget()
        form = QVBoxLayout(time_form)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)
        form.addWidget(self._time_edit)
        form.addWidget(self._labeled("本地时间", self._time_local))
        form.addWidget(self._labeled("秒时间戳", self._time_seconds))
        form.addWidget(self._labeled("毫秒时间戳", self._time_millis))
        form.addStretch(1)
        self.stack.addWidget(
            self._panel(
                None,
                [
                    ("现在", self._time_now),
                    ("转时间戳", self._time_to_stamp),
                    ("转时间", self._stamp_to_time),
                    ("复制秒", lambda: self._copy(self._time_seconds.text())),
                ],
                extra=(time_form,),
            )
        )
        self.stack.addWidget(
            self._panel(
                None,
                [
                    ("URL 编码", lambda: self._run_codec(encode_url)),
                    ("URL 解码", lambda: self._run_codec(decode_url)),
                    ("Base64 编码", lambda: self._run_codec(encode_base64)),
                    ("Base64 解码", lambda: self._run_codec(decode_base64)),
                    ("复制", lambda: self._copy(self._codec_out.toPlainText())),
                ],
                extra=(self._codec_in, self._codec_out),
            )
        )
        self.stack.addWidget(
            self._panel(
                None,
                [
                    ("MD5", lambda: self._run_hash(hash_md5)),
                    ("SHA256", lambda: self._run_hash(hash_sha256)),
                    ("UUID", self._fill_uuid),
                    ("复制", lambda: self._copy(self._hash_out.toPlainText())),
                ],
                extra=(self._hash_in, self._hash_out),
            )
        )
        self.stack.addWidget(
            self._panel(
                None,
                [
                    ("本地转换", self._alias_local),
                    ("AI 起名", self._alias_ai),
                    ("复制", lambda: self._copy(self._alias_out.toPlainText())),
                ],
                extra=(self._alias_in, self._alias_out),
            )
        )
        almanac_form = QWidget()
        almanac_layout = QVBoxLayout(almanac_form)
        almanac_layout.setContentsMargins(0, 0, 0, 0)
        almanac_layout.setSpacing(6)
        almanac_layout.addWidget(self._almanac_date)
        almanac_layout.addWidget(self._almanac_out, 1)
        self.stack.addWidget(
            self._panel(
                None,
                [
                    ("今天", self._almanac_today),
                    ("查黄历", self._almanac_lookup),
                    ("复制", lambda: self._copy(self._almanac_out.toPlainText())),
                ],
                extra=(almanac_form,),
            )
        )

        self.status = QLabel()
        self.status.hide()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        root.addLayout(chip_row)
        root.addWidget(self.stack, 1)
        root.addWidget(self.status)
        self._apply_styles()
        self._set_tool("json")

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._apply_styles()
        self._set_tool(self._current)

    def _apply_styles(self) -> None:
        self.status.setStyleSheet(f"color: {self._theme.text_secondary}; font-size: 12px;")

    def _text(self, placeholder: str) -> QPlainTextEdit:
        edit = QPlainTextEdit()
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(90)
        return edit

    def _labeled(self, title: str, widget: QWidget) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        caption = QLabel(title)
        caption.setStyleSheet(f"color: {self._theme.text_secondary}; font-size: 12px;")
        layout.addWidget(caption)
        layout.addWidget(widget)
        widget.setProperty("caption", caption)
        return box

    def _panel(self, editor: QPlainTextEdit | None, actions: list[tuple[str, object]], extra=()) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        if editor is not None:
            layout.addWidget(editor, 1)
        for widget in extra:
            layout.addWidget(widget, 1)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        for label, slot in actions:
            button = QPushButton(label)
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(30)
            button.clicked.connect(slot)
            row.addWidget(button)
        layout.addLayout(row)
        return page

    def _set_tool(self, key: str) -> None:
        keys = [item[0] for item in TOOLS]
        self._current = key if key in self._tool_buttons else "json"
        self.stack.setCurrentIndex(keys.index(self._current))
        for name, button in self._tool_buttons.items():
            style_chip(button, self._theme, name == self._current)
        self._set_status("")

    def _set_status(self, text: str) -> None:
        self.status.setText(text)
        self.status.setVisible(bool(text))

    def _copy(self, text: str) -> None:
        if not text.strip():
            self._set_status("没有可复制的内容")
            return
        QGuiApplication.clipboard().setText(text)
        self._set_status("已复制")

    def _format_json(self) -> None:
        self._apply_transform(self._json_edit, format_json)

    def _minify_json(self) -> None:
        self._apply_transform(self._json_edit, minify_json)

    def _apply_transform(self, editor: QPlainTextEdit, func) -> None:
        try:
            editor.setPlainText(func(editor.toPlainText()))
            self._set_status("完成")
        except ToolsError as exc:
            self._set_status(str(exc))

    def _run_codec(self, func) -> None:
        try:
            self._codec_out.setPlainText(func(self._codec_in.toPlainText()))
            self._set_status("完成")
        except ToolsError as exc:
            self._set_status(str(exc))

    def _run_hash(self, func) -> None:
        self._hash_out.setPlainText(func(self._hash_in.toPlainText()))
        self._set_status("完成")

    def _fill_uuid(self) -> None:
        self._hash_out.setPlainText(new_uuid())
        self._set_status("已生成 UUID")

    def _fill_time(self, dt: datetime) -> None:
        snap = time_snapshot(dt)
        self._time_local.setText(snap["local"])
        self._time_seconds.setText(snap["seconds"])
        self._time_millis.setText(snap["millis"])

    def _time_now(self) -> None:
        now = datetime.now()
        self._time_edit.setText(now.strftime("%Y-%m-%d %H:%M:%S"))
        self._fill_time(now)
        self._set_status("当前时间")

    def _time_to_stamp(self) -> None:
        try:
            self._fill_time(parse_time_value(self._time_edit.text()))
            self._set_status("已转为时间戳")
        except ToolsError as exc:
            self._set_status(str(exc))

    def _stamp_to_time(self) -> None:
        try:
            dt = parse_time_value(self._time_edit.text())
            self._fill_time(dt)
            self._time_edit.setText(dt.strftime("%Y-%m-%d %H:%M:%S"))
            self._set_status("已转为时间")
        except ToolsError as exc:
            self._set_status(str(exc))

    def _selected_model(self):
        model_id = self._ctx.settings.settings.default_ai_model
        models = self._ctx.reports.models()
        if model_id is not None:
            found = next((item for item in models if item.id == model_id), None)
            if found is not None:
                return found
        return models[0] if models else None

    def _translate(self, target: str) -> None:
        text = self._zh_edit.toPlainText().strip()
        if not text:
            self._set_status("请输入要翻译的文本")
            return
        lang = "英文" if target == "en" else "中文"
        history = [{"role": "user", "content": f"请将下面内容译成{lang}：\n{text}"}]
        self._run_ai(history, TRANSLATE_SYSTEM_PROMPT, self._on_translated, self._on_translate_fail, "正在翻译…")

    def _run_ai(self, history, system: str, on_ok, on_fail, busy_text: str) -> None:
        if self._thread and self._thread.isRunning():
            return
        config = self._selected_model()
        if config is None:
            QMessageBox.information(self, "提示", "请先在设置中配置 AI 模型")
            return
        self._set_status(busy_text)
        thread = QThread(self)
        worker = _AIWorker(lambda cfg=config, payload=history, prompt=system: self._ctx.ai.ask(cfg, payload, prompt))
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(on_ok)
        worker.failed.connect(on_fail)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _on_translated(self, text: str) -> None:
        self._en_edit.setPlainText(text.strip())
        self._set_status("翻译完成")

    def _on_translate_fail(self, message: str) -> None:
        self._set_status("翻译失败")
        QMessageBox.warning(self, "翻译失败", message)

    def _show_naming(self, parts: list[str]) -> None:
        self._alias_out.setPlainText(format_naming(naming_styles(parts)))
        self._set_status("完成")

    def _alias_local(self) -> None:
        try:
            self._show_naming(split_identifier(self._alias_in.toPlainText()))
        except ToolsError as exc:
            self._set_status(str(exc))

    def _alias_ai(self) -> None:
        text = self._alias_in.toPlainText().strip()
        if not text:
            self._set_status("请输入中文含义或英文变量名")
            return
        history = [{"role": "user", "content": text}]
        self._run_ai(history, NAME_SYSTEM_PROMPT, self._on_named, self._on_name_fail, "正在起名…")

    def _on_named(self, text: str) -> None:
        try:
            self._show_naming(parse_name_words(text))
        except ToolsError as exc:
            self._set_status(str(exc))

    def _on_name_fail(self, message: str) -> None:
        self._set_status("起名失败")
        QMessageBox.warning(self, "起名失败", message)

    def _parse_almanac_day(self) -> date:
        raw = self._almanac_date.text().strip()
        if not raw or raw in {"今天", "today"}:
            return date.today()
        return parse_time_value(raw).date()

    def _almanac_today(self) -> None:
        today = date.today()
        self._almanac_date.setText(today.strftime("%Y-%m-%d"))
        self._almanac_out.setPlainText(almanac_for(today))
        self._set_status("今日黄历")

    def _almanac_lookup(self) -> None:
        try:
            day = self._parse_almanac_day()
            self._almanac_date.setText(day.strftime("%Y-%m-%d"))
            self._almanac_out.setPlainText(almanac_for(day))
            self._set_status("完成")
        except ToolsError as exc:
            self._set_status(str(exc))
