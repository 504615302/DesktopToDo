from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPlainTextEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from model.memo import Memo
from service.memo_service import MemoService
from ui.datetime_picker import IconButton
from ui.icons import asset_pixmap, stroke_icon
from ui.page_utils import clear_layout, empty_label, make_scroll
from ui.styles import Theme
from ui.submit_edit import SubmitTextEdit


def _shorten(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _card_texts(memo: Memo) -> tuple[str, str, str]:
    lines = [line.strip() for line in memo.content.splitlines() if line.strip()]
    title = memo.title.strip() or (lines[0] if lines else "未命名备忘")
    preview = ""
    if lines:
        preview = lines[0] if title != lines[0] else (lines[1] if len(lines) > 1 else "")
    stamp = memo.updated_at or memo.created_at
    date_text = stamp.strftime("%m-%d") if stamp else ""
    return _shorten(title, 22), _shorten(preview, 28), date_text


class MemoCard(QWidget):
    selected = Signal(object)
    pin_requested = Signal(object)
    delete_requested = Signal(object)
    report_toggled = Signal(object)

    def __init__(self, memo: Memo, theme: Theme, active: bool, parent=None):
        super().__init__(parent)
        self.memo = memo
        self._theme = theme
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("memoCard")
        self.setMinimumHeight(64)
        title_text, preview_text, date_text = _card_texts(memo)

        title = QLabel(title_text)
        title.setWordWrap(False)
        title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        title.setStyleSheet(f"color: {theme.text}; font-size: 13px; font-weight: 600;")

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(6)
        top.addWidget(title, 1)
        if memo.is_pinned:
            pin = QLabel()
            pin.setPixmap(stroke_icon("pinned", theme.accent, 14).pixmap(14, 14))
            pin.setFixedSize(16, 16)
            top.addWidget(pin, 0, Qt.AlignTop)

        preview = QLabel(preview_text or "暂无正文")
        preview.setWordWrap(False)
        preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        preview.setStyleSheet(f"color: {theme.text_secondary}; font-size: 12px;")

        meta_bits = [part for part in (memo.tags.strip(), date_text) if part]
        meta = QLabel("  ·  ".join(meta_bits) if meta_bits else memo.category)
        meta.setStyleSheet(f"color: {theme.text_muted}; font-size: 11px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)
        layout.addLayout(top)
        layout.addWidget(preview)
        layout.addWidget(meta)

        border = theme.accent if active else theme.border
        bg = theme.chip_active if active else theme.surface
        self.setStyleSheet(
            f"""
            #memoCard {{
                background: {bg};
                border: 1px solid {border};
                border-radius: {max(10, theme.chip_radius)}px;
            }}
            """
        )

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.selected.emit(self.memo)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        pin = menu.addAction("取消置顶" if self.memo.is_pinned else "置顶")
        report = menu.addAction("从周报素材移除" if self.memo.include_in_report else "加入周报")
        delete = menu.addAction("删除")
        chosen = menu.exec(event.globalPos())
        if chosen is pin:
            self.pin_requested.emit(self.memo)
        elif chosen is report:
            self.report_toggled.emit(self.memo)
        elif chosen is delete:
            self.delete_requested.emit(self.memo)


class MemoPage(QWidget):
    changed = Signal()

    def __init__(self, theme: Theme, memos: MemoService, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._memos = memos
        self._current: Memo | None = None
        self._loading = False

        head = QHBoxLayout()
        head.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索备忘")
        self.search.setFixedHeight(34)
        self.search.textChanged.connect(self.reload)
        self.add_btn = IconButton("plus", theme.accent, "新增备忘", 32, 16)
        self.add_btn.clicked.connect(self.create_memo)
        head.addWidget(self.search, 1)
        head.addWidget(self.add_btn)

        self.list_caption = QLabel()
        self.caption_icon = QLabel()
        self.caption_icon.setFixedSize(16, 16)
        self.caption_icon.setPixmap(asset_pixmap("nav_memo", 16))
        caption_row = QHBoxLayout()
        caption_row.setContentsMargins(2, 0, 2, 0)
        caption_row.setSpacing(6)
        caption_row.addWidget(self.caption_icon)
        caption_row.addWidget(self.list_caption, 1)
        host = QWidget()
        self.list_layout = QVBoxLayout(host)
        self.list_layout.setContentsMargins(0, 0, 4, 0)
        self.list_layout.setSpacing(8)
        self.scroll = make_scroll(host)
        self.scroll.setMinimumHeight(140)

        self.editor_panel = QWidget()
        self.editor_panel.setObjectName("memoEditor")
        self.editor_panel.setAttribute(Qt.WA_StyledBackground, True)
        panel = QVBoxLayout(self.editor_panel)
        panel.setContentsMargins(12, 10, 12, 10)
        panel.setSpacing(8)

        title_row = QHBoxLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("标题（可选）")
        self.status = QLabel()
        title_row.addWidget(self.title_edit, 1)
        title_row.addWidget(self.status)

        self.editor = SubmitTextEdit()
        self.editor.setPlaceholderText("写下备忘，Enter 换行，Ctrl+Enter 保存")
        self.editor.setFrameStyle(QPlainTextEdit.NoFrame)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("#工作 #开发")
        self.pin_check = QCheckBox("置顶")
        self.report_check = QCheckBox("周报")
        self.report_check.setChecked(True)
        footer.addWidget(self.tags_edit, 1)
        footer.addWidget(self.pin_check)
        footer.addWidget(self.report_check)

        panel.addLayout(title_row)
        panel.addWidget(self.editor, 1)
        panel.addLayout(footer)

        for widget in (self.title_edit, self.editor, self.tags_edit):
            widget.textChanged.connect(self._on_edit)
        self.title_edit.returnPressed.connect(self._save_from_enter)
        self.tags_edit.returnPressed.connect(self._save_from_enter)
        self.editor.submit_requested.connect(self._save_from_enter)
        self.pin_check.toggled.connect(self._on_flag_changed)
        self.report_check.toggled.connect(self._on_flag_changed)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        root.addLayout(head)
        root.addLayout(caption_row)
        root.addWidget(self.scroll, 2)
        root.addWidget(self.editor_panel, 3)
        self._apply_editor_style()
        self.reload()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.add_btn.set_color(theme.accent)
        self.caption_icon.setPixmap(asset_pixmap("nav_memo", 16))
        self._apply_editor_style()
        self.reload()

    def _apply_editor_style(self) -> None:
        theme = self._theme
        self.list_caption.setStyleSheet(
            f"color: {theme.text_muted}; font-size: 12px; font-weight: 600; padding: 0 2px;"
        )
        self.status.setStyleSheet(f"color: {theme.text_muted}; font-size: 11px;")
        radius = max(10, theme.chip_radius)
        self.editor_panel.setStyleSheet(
            f"""
            QWidget#memoEditor {{
                background: {theme.surface};
                border: 1px solid {theme.border};
                border-radius: {radius}px;
            }}
            QWidget#memoEditor QLineEdit,
            QWidget#memoEditor QPlainTextEdit {{
                background: transparent;
                border: none;
                padding: 0;
            }}
            QWidget#memoEditor QLineEdit:focus,
            QWidget#memoEditor QPlainTextEdit:focus {{
                border: none;
            }}
            """
        )

    def hideEvent(self, event) -> None:
        if not self._loading:
            self.flush()
        super().hideEvent(event)

    def create_memo(self) -> None:
        self.flush()
        self._load(None)
        self.editor.setFocus()

    def open_memo(self, memo: Memo) -> None:
        self.flush()
        self._load(memo)

    def flush(self) -> None:
        self._save(finish_new=False)

    def reload(self, *_args) -> None:
        keep_id = self._current.id if self._current else None
        memos = self._memos.search(self.search.text())
        self.list_caption.setText(f"全部备忘  {len(memos)}" if memos else "全部备忘")
        clear_layout(self.list_layout)
        if not memos:
            self.list_layout.addWidget(empty_label("还没有备忘，在下方输入后按 Ctrl+Enter 保存", self._theme))
            self.list_layout.addStretch()
            return
        for memo in memos:
            card = MemoCard(memo, self._theme, keep_id == memo.id)
            card.selected.connect(self.open_memo)
            card.pin_requested.connect(self._toggle_pin)
            card.delete_requested.connect(self._delete)
            card.report_toggled.connect(self._toggle_report)
            self.list_layout.addWidget(card)
        self.list_layout.addStretch()
        if keep_id:
            found = next((item for item in memos if item.id == keep_id), None)
            if found:
                self._current = found

    def _load(self, memo: Memo | None) -> None:
        self._loading = True
        self._current = memo
        self.title_edit.setText(memo.title if memo else "")
        self.editor.setPlainText(memo.content if memo else "")
        self.tags_edit.setText(memo.tags if memo else "")
        self.pin_check.setChecked(bool(memo and memo.is_pinned))
        self.report_check.setChecked(True if memo is None else memo.include_in_report)
        self.status.setText("Ctrl+Enter 保存")
        self._loading = False
        self.reload()

    def _on_edit(self, *_args) -> None:
        if self._loading:
            return
        self.status.setText("未保存")

    def _on_flag_changed(self, *_args) -> None:
        if self._loading:
            return
        if self._current is None:
            self.status.setText("未保存")
            return
        self._save(finish_new=False)

    def _save_from_enter(self) -> None:
        self._save(finish_new=True)

    def _save(self, *, finish_new: bool) -> bool:
        if self._loading:
            return False
        content = self.editor.toPlainText().strip()
        title = self.title_edit.text().strip()
        tags = self.tags_edit.text().strip()
        if not content:
            if title and self._current is None:
                content = title
                title = ""
                self._loading = True
                self.editor.setPlainText(content)
                self.title_edit.clear()
                self._loading = False
            else:
                if not finish_new:
                    return False
                self.status.setText("写点内容再保存")
                return False
        try:
            created = self._current is None
            if created:
                self._current = self._memos.add_memo(
                    content,
                    title=title,
                    tags=tags,
                    include_in_report=self.report_check.isChecked(),
                )
                self._current.is_pinned = self.pin_check.isChecked()
                if self._current.is_pinned:
                    self._current = self._memos.update_memo(self._current)
            else:
                self._current.title = title
                self._current.content = content
                self._current.tags = tags
                self._current.is_pinned = self.pin_check.isChecked()
                self._current.include_in_report = self.report_check.isChecked()
                self._current = self._memos.update_memo(self._current)
            self.status.setText("已保存")
            self.changed.emit()
            self.reload()
            if created and finish_new:
                self.editor.setFocus()
            return True
        except ValueError:
            self.status.setText("内容不能为空")
            return False

    def _toggle_pin(self, memo: Memo) -> None:
        self.flush()
        self._memos.set_pinned(memo, not memo.is_pinned)
        if self._current and self._current.id == memo.id:
            self._current.is_pinned = not memo.is_pinned
            self._loading = True
            self.pin_check.setChecked(self._current.is_pinned)
            self._loading = False
        self.changed.emit()
        self.reload()

    def _toggle_report(self, memo: Memo) -> None:
        self.flush()
        self._memos.set_include_in_report(memo, not memo.include_in_report)
        self.changed.emit()
        self.reload()

    def _delete(self, memo: Memo) -> None:
        self._memos.delete_memo(memo.id)
        if self._current and self._current.id == memo.id:
            self._load(None)
        self.changed.emit()
        self.reload()
