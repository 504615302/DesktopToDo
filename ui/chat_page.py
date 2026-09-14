from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from service.ai_service import AIClientError
from service.app_context import AppContext
from service.chat_service import build_qa_context
from ui.chat_model_dialog import ChatModelDialog
from ui.datetime_picker import IconButton
from ui.icons import stroke_icon
from ui.page_utils import empty_label, make_scroll, style_chip
from ui.styles import Theme
from ui.submit_edit import SubmitTextEdit

HINTS = {
    "cute": "问问今天先做什么，或让我帮你理一理待办 ✦",
    "business": "可询问工作安排、待办重点或备忘内容",
    "minimal": "输入问题，可选中待办 / 备忘作为上下文",
    "tech": "向终端提问，可带上待办与备忘",
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


class ChatBubble(QWidget):
    def __init__(self, text: str, mine: bool, theme: Theme, parent=None):
        super().__init__(parent)
        body = QLabel(text)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        body.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        radius = max(10, theme.chip_radius)
        bg = theme.accent_soft if mine else theme.surface
        body.setStyleSheet(
            f"""
            QLabel {{
                background: {bg};
                color: {theme.text};
                border: 1px solid {theme.border};
                border-radius: {radius}px;
                padding: 8px 10px;
                font-size: 13px;
            }}
            """
        )
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        if mine:
            row.addStretch(1)
            row.addWidget(body, 4)
        else:
            row.addWidget(body, 4)
            row.addStretch(1)


class ChatPage(QWidget):
    layout_changed = Signal()

    def __init__(self, theme: Theme, ctx: AppContext, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._ctx = ctx
        self._history: list[dict] = []
        self._thread: QThread | None = None
        self._worker: _AIWorker | None = None
        self._compact = False
        self._model_id = None
        self._qa_temperature: float | None = None
        self._qa_max_tokens: int | None = None

        self.model_btn = QPushButton("选择模型")
        self.model_btn.setCursor(Qt.PointingHandCursor)
        self.model_btn.setFixedHeight(32)
        self.model_btn.setToolTip("选择模型并调节参数")
        self.model_btn.clicked.connect(self._open_model_dialog)
        self.clear_btn = IconButton("delete", theme.text_secondary, "清空对话", 32, 16)
        self.clear_btn.clicked.connect(self.clear_chat)
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)
        top.addWidget(self.model_btn, 1)
        top.addWidget(self.clear_btn)

        ctx_row = QHBoxLayout()
        ctx_row.setContentsMargins(0, 0, 0, 0)
        ctx_row.setSpacing(6)
        self.ctx_tasks = QPushButton("待办")
        self.ctx_memos = QPushButton("备忘")
        for button, checked in ((self.ctx_tasks, True), (self.ctx_memos, False)):
            button.setCheckable(True)
            button.setChecked(checked)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(self._refresh_chips)
            ctx_row.addWidget(button)
        ctx_row.addStretch()

        self.chrome = QWidget()
        chrome_layout = QVBoxLayout(self.chrome)
        chrome_layout.setContentsMargins(0, 0, 0, 0)
        chrome_layout.setSpacing(8)
        chrome_layout.addLayout(top)
        chrome_layout.addLayout(ctx_row)

        host = QWidget()
        self.list_layout = QVBoxLayout(host)
        self.list_layout.setContentsMargins(0, 0, 4, 0)
        self.list_layout.setSpacing(8)
        self.scroll = make_scroll(host)

        self._ask_icon = QLabel()
        self._ask_icon.setFixedSize(18, 18)
        self._ask_icon.hide()
        self.input = SubmitTextEdit()
        self.input.setFixedHeight(52)
        self.input.setTabChangesFocus(True)
        self.input.submit_requested.connect(self.send)
        self.send_btn = QPushButton("提问")
        self.send_btn.setObjectName("primaryButton")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setFixedHeight(36)
        self.send_btn.clicked.connect(self.send)
        self.compact_model_btn = IconButton("settings", theme.text_secondary, "选择模型与参数", 36, 16)
        self.compact_model_btn.clicked.connect(self._open_model_dialog)
        self.compact_model_btn.hide()
        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(8)
        input_row.addWidget(self._ask_icon)
        input_row.addWidget(self.input, 1)
        input_row.addWidget(self.compact_model_btn)
        input_row.addWidget(self.send_btn)

        self.status = QLabel()
        self.status.hide()

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(8)
        self._root.addWidget(self.chrome)
        self._root.addWidget(self.scroll, 1)
        self._root.addWidget(self.status)
        self._root.addLayout(input_row)

        self._apply_styles()
        self.reload_options()
        self._reset_empty()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._apply_styles()
        self._rebuild_bubbles()

    def set_compact(self, compact: bool) -> None:
        self._compact = compact
        self._sync_compact_view()
        if compact:
            self.focus_input()

    def focus_input(self) -> None:
        self.input.setFocus()
        self.input.selectAll()

    def compact_height(self) -> int:
        spacing = self._root.spacing()
        height = max(36, self.input.height())
        if self.status.isVisible():
            height += spacing + max(16, self.status.sizeHint().height())
        if self.scroll.isVisible():
            host = self.scroll.widget()
            content = host.sizeHint().height() if host is not None else 0
            height += spacing + min(max(content, 48), 280)
        return height

    def _has_messages(self) -> bool:
        return any(item.get("visible") for item in self._history)

    def _sync_compact_view(self) -> None:
        compact = self._compact
        self.chrome.setVisible(not compact)
        self.send_btn.setVisible(not compact)
        self._ask_icon.setVisible(compact)
        self.compact_model_btn.setVisible(compact)
        self._root.setStretch(self._root.indexOf(self.scroll), 0 if compact else 1)
        if compact:
            self.scroll.setVisible(self._has_messages())
            if not self._has_messages():
                self._clear_list()
            self.input.setPlaceholderText("输入问题，Enter 换行，Ctrl+Enter 提问")
        else:
            self.scroll.show()
            self.input.setPlaceholderText(HINTS.get(self._theme.name, HINTS["minimal"]))
            if not self._has_messages():
                self._reset_empty()
        self.layout_changed.emit()

    def _apply_styles(self) -> None:
        theme = self._theme
        self.clear_btn.set_color(theme.text_secondary)
        self.compact_model_btn.set_color(theme.text_secondary)
        self.status.setStyleSheet(f"color: {theme.text_secondary}; font-size: 12px;")
        self.send_btn.setIcon(stroke_icon("sparkle", theme.primary_text, 16))
        self._ask_icon.setPixmap(stroke_icon("sparkle", theme.accent, 16).pixmap(16, 16))
        if self._compact:
            self.input.setPlaceholderText("输入问题，Enter 换行，Ctrl+Enter 提问")
        else:
            self.input.setPlaceholderText(HINTS.get(theme.name, HINTS["minimal"]))
        self._refresh_chips()

    def _refresh_chips(self) -> None:
        style_chip(self.ctx_tasks, self._theme, self.ctx_tasks.isChecked())
        style_chip(self.ctx_memos, self._theme, self.ctx_memos.isChecked())

    def reload_options(self) -> None:
        settings = self._ctx.settings.settings
        models = self._ctx.reports.models()
        self._model_id = settings.default_ai_model
        if self._model_id is None and models:
            self._model_id = models[0].id
        elif self._model_id is not None and not any(item.id == self._model_id for item in models):
            self._model_id = models[0].id if models else None
        self._qa_temperature = settings.qa_temperature
        self._qa_max_tokens = settings.qa_max_tokens
        self._refresh_model_button()

    def _open_model_dialog(self) -> None:
        config = self._selected_model()
        temperature, max_tokens = self._effective_params(config)
        dialog = ChatModelDialog(
            self._theme,
            self._ctx.reports,
            self._model_id,
            temperature,
            max_tokens,
            self.window(),
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        self._model_id = dialog.model_id
        self._qa_temperature = dialog.temperature
        self._qa_max_tokens = dialog.max_tokens
        self._ctx.settings.update(
            default_ai_model=self._model_id,
            qa_temperature=self._qa_temperature,
            qa_max_tokens=self._qa_max_tokens,
        )
        self._refresh_model_button()

    def _refresh_model_button(self) -> None:
        config = self._selected_model()
        if config is None:
            self.model_btn.setText("选择模型")
            self.compact_model_btn.setToolTip("选择模型与参数")
            return
        temperature, max_tokens = self._effective_params(config)
        self.model_btn.setText(f"{config.name}  ·  {temperature:.1f} / {max_tokens}")
        self.compact_model_btn.setToolTip(f"{config.name}  ·  温度 {temperature:.2f}  ·  {max_tokens} tokens")

    def _effective_params(self, config) -> tuple[float, int]:
        temperature = config.temperature if config is not None else 0.3
        max_tokens = config.max_tokens if config is not None else 1024
        if self._qa_temperature is not None:
            temperature = self._qa_temperature
        if self._qa_max_tokens is not None:
            max_tokens = self._qa_max_tokens
        return temperature, max_tokens

    def clear_chat(self) -> None:
        self._history.clear()
        self._set_status("")
        self._reset_empty()

    def _reset_empty(self) -> None:
        self._clear_list()
        if self._compact:
            self.scroll.hide()
            self.layout_changed.emit()
            return
        hint = HINTS.get(self._theme.name, HINTS["minimal"])
        self.list_layout.addWidget(empty_label(hint, self._theme))
        self.list_layout.addStretch()
        self.layout_changed.emit()

    def _clear_list(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _rebuild_bubbles(self) -> None:
        visible = [item for item in self._history if item.get("visible")]
        if not visible:
            self._reset_empty()
            return
        self._clear_list()
        for item in visible:
            self.list_layout.addWidget(ChatBubble(item["display"], item["role"] == "user", self._theme))
        self.list_layout.addStretch()
        if self._compact:
            self.scroll.show()
        QTimer.singleShot(0, self._after_bubbles)
        self.layout_changed.emit()

    def _after_bubbles(self) -> None:
        self._scroll_bottom()
        self.layout_changed.emit()

    def _scroll_bottom(self) -> None:
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def send(self) -> None:
        question = self.input.toPlainText().strip()
        if not question:
            return
        if self._thread and self._thread.isRunning():
            return
        config = self._selected_model()
        if config is None:
            self._open_model_dialog()
            config = self._selected_model()
            if config is None:
                return
        temperature, max_tokens = self._effective_params(config)
        config = replace(config, temperature=temperature, max_tokens=max_tokens)
        context = build_qa_context(
            self._ctx.tasks.list_tasks(),
            self._ctx.memos.list_memos(),
            include_tasks=self.ctx_tasks.isChecked(),
            include_memos=self.ctx_memos.isChecked(),
        )
        api_text = question
        if context:
            api_text = f"【应用上下文】\n{context}\n\n【用户问题】\n{question}"
        self._history.append({"role": "user", "content": api_text, "display": question, "visible": True})
        self._history = self._history[-12:]
        self.input.clear()
        self._rebuild_bubbles()
        self._set_status("正在思考…")
        self._set_busy(True)
        payload = [{"role": item["role"], "content": item["content"]} for item in self._history]
        thread = QThread(self)
        worker = _AIWorker(lambda cfg=config, history=payload: self._ctx.ai.ask(cfg, history))
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_done)
        worker.failed.connect(self._on_fail)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(lambda: self._set_busy(False))
        self._thread = thread
        self._worker = worker
        thread.start()

    def _selected_model(self):
        return next((item for item in self._ctx.reports.models() if item.id == self._model_id), None)

    def _on_done(self, text: str) -> None:
        self._history.append({"role": "assistant", "content": text, "display": text, "visible": True})
        self._set_status("")
        self._rebuild_bubbles()

    def _on_fail(self, message: str) -> None:
        if self._history and self._history[-1]["role"] == "user":
            self._history.pop()
        self._rebuild_bubbles()
        self._set_status("回答失败")
        QMessageBox.warning(self, "AI 调用失败", message)

    def _set_status(self, text: str) -> None:
        self.status.setText(text)
        self.status.setVisible(bool(text))
        self.layout_changed.emit()

    def _set_busy(self, busy: bool) -> None:
        self.send_btn.setEnabled(not busy)
        self.input.setEnabled(not busy)
        self.clear_btn.setEnabled(not busy)
        self.model_btn.setEnabled(not busy)
        self.compact_model_btn.setEnabled(not busy)
