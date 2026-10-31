# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ui.icons import stroke_icon
from ui.styles import Theme

MAX_LOCAL_SIZE = 20 * 1024 * 1024
CHAPTER_PATTERN = re.compile(
    r"^\s*(?:第\s*[0-9零一二两三四五六七八九十百千万亿]+\s*[章节卷回幕部集]"
    r"|序章|序言|楔子|尾声|终章|番外(?:[0-9零一二两三四五六七八九十百千万亿]+)?)\s*[^\n]{0,40}$",
    re.MULTILINE,
)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    lines = [line.rstrip() for line in text.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def split_chapters(text: str) -> list[tuple[str, str]]:
    normalized = normalize_text(text)
    matches = list(CHAPTER_PATTERN.finditer(normalized))
    if len(matches) < 2:
        return [("正文", normalized)] if normalized else []

    chapters: list[tuple[str, str]] = []
    if matches[0].start() > 0:
        intro = normalized[: matches[0].start()].strip()
        if intro:
            chapters.append(("开篇", intro))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        chunk = normalized[match.start() : end].strip()
        title = chunk.split("\n", 1)[0].strip()[:60]
        chapters.append((title, chunk))
    return chapters


def _chinese_score(text: str) -> int:
    common = set(
        "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争美阶油思术极交受联什认六共权收证改清再画"
    )
    cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    hits = sum(1 for char in text if char in common)
    suspicious = sum(
        1
        for char in text
        if "\u0250" <= char <= "\u036f"
        or "\u0400" <= char <= "\u04ff"
        or "\ue000" <= char <= "\uf8ff"
    )
    return hits * 8 + cjk - suspicious * 4


def decode_bytes(raw: bytes) -> str:
    encodings = []
    if raw.startswith(b"\xef\xbb\xbf"):
        encodings.append("utf-8-sig")
    elif raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        encodings.append("utf-16")
    encodings.extend(("utf-8", "gb18030", "big5"))

    candidates: list[str] = []
    for encoding in dict.fromkeys(encodings):
        try:
            candidates.append(raw.decode(encoding))
        except (UnicodeDecodeError, LookupError):
            continue
    if not candidates:
        raise ValueError("无法识别文件编码")
    if len(candidates) == 1:
        return candidates[0]
    return max(candidates, key=_chinese_score)


class NovelPanel(QWidget):
    pure_mode_changed = Signal(bool)

    def __init__(self, theme: Theme, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._chapters: list[tuple[str, str]] = []
        self._chapter_index = 0
        self._font_size = 17
        self._pure_mode = False
        self._scroll_animation: QPropertyAnimation | None = None
        self._scroll_target = 0

        self.title_label = QLabel("本地小说阅读")
        self.open_file_button = QPushButton("选择 TXT/MD 文件")
        self.open_file_button.setFixedHeight(34)
        self.open_file_button.clicked.connect(self.open_file)
        self.head_bar = QWidget()
        head = QHBoxLayout(self.head_bar)
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(8)
        head.addWidget(self.title_label, 1)
        head.addWidget(self.open_file_button)

        self.reader = QPlainTextEdit()
        self.reader.setReadOnly(True)
        self.reader.setFocusPolicy(Qt.StrongFocus)
        self.reader.setFrameStyle(QPlainTextEdit.NoFrame)
        self.reader.setPlainText("选择一个本地 TXT 或 MD 文件开始阅读。")
        self.reader.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.reader.verticalScrollBar().valueChanged.connect(self._update_progress)
        self.reader.viewport().installEventFilter(self)

        self.chapter_combo = QComboBox()
        self.chapter_combo.setMinimumWidth(130)
        self.chapter_combo.currentIndexChanged.connect(self._on_chapter_selected)
        self.prev_button = QPushButton("上一章")
        self.next_button = QPushButton("下一章")
        self.smaller_button = QPushButton("A-")
        self.larger_button = QPushButton("A+")
        self.pure_button = QPushButton("纯净模式")
        self.pure_button.setToolTip("切换纯净模式")
        for button in (
            self.smaller_button,
            self.larger_button,
        ):
            button.setFixedHeight(30)
        for button in (self.prev_button, self.next_button, self.pure_button):
            button.setFixedSize(38, 36)
            button.setIconSize(QSize(20, 20))
        self.prev_button.clicked.connect(lambda: self._move_chapter(-1))
        self.next_button.clicked.connect(lambda: self._move_chapter(1))
        self.smaller_button.clicked.connect(lambda: self._set_font_size(self._font_size - 1))
        self.larger_button.clicked.connect(lambda: self._set_font_size(self._font_size + 1))
        self.pure_button.clicked.connect(
            lambda: self.set_pure_mode(not self._pure_mode)
        )

        self.progress_label = QLabel("0%")
        self.progress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_label = QLabel()
        self.status_label.hide()
        self.footer_bar = QWidget()
        self.footer_bar.setObjectName("novelFooter")
        footer = QVBoxLayout(self.footer_bar)
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(4)

        self.footer_context_bar = QWidget()
        context_row = QHBoxLayout(self.footer_context_bar)
        context_row.setContentsMargins(0, 0, 0, 0)
        context_row.setSpacing(8)
        context_row.addWidget(self.chapter_combo, 1)
        context_row.addWidget(self.progress_label)

        self.footer_action_bar = QWidget()
        action_row = QHBoxLayout(self.footer_action_bar)
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(6)
        self.footer_stretch = action_row.addStretch(0)
        action_row.addWidget(self.prev_button)
        action_row.addWidget(self.next_button)
        action_row.addWidget(self.smaller_button)
        action_row.addWidget(self.larger_button)
        action_row.addWidget(self.pure_button)

        self.font_size_label = QLabel("字号")
        self.font_size_value = QLabel(f"{self._font_size}px")
        self.font_size_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.font_size_value.setMinimumWidth(42)
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(12, 28)
        self.font_size_slider.setValue(self._font_size)
        self.font_size_slider.setToolTip("调整阅读字号")
        self.font_size_slider.valueChanged.connect(self._set_font_size)
        self.font_row = QWidget()
        self.font_row.setObjectName("novelFontRow")
        font_row = QHBoxLayout(self.font_row)
        font_row.setContentsMargins(28, 8, 28, 12)
        font_row.setSpacing(12)
        font_row.addWidget(self.font_size_label)
        font_row.addWidget(self.font_size_slider, 1)
        font_row.addWidget(self.font_size_value)
        self.font_row.hide()

        footer.addWidget(self.footer_context_bar)
        footer.addWidget(self.footer_action_bar)
        footer.addWidget(self.font_row)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        root.addWidget(self.head_bar)
        root.addWidget(self.reader, 1)
        root.addWidget(self.status_label)
        root.addWidget(self.footer_bar)
        self._apply_reading_chrome()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._apply_reading_chrome()

    def is_pure_mode(self) -> bool:
        return self._pure_mode

    def handle_key(self, event) -> bool:
        key = event.key()
        if key == Qt.Key.Key_Left:
            self._move_chapter(-1)
            return True
        if key == Qt.Key.Key_Right:
            self._move_chapter(1)
            return True
        if key in {Qt.Key.Key_Up, Qt.Key.Key_Down}:
            if (
                event.isAutoRepeat()
                and self._scroll_animation is not None
                and self._scroll_animation.state() == QPropertyAnimation.State.Running
            ):
                return True

            line_height = max(18.0, float(self.reader.fontMetrics().lineSpacing()))
            viewport_height = max(1.0, float(self.reader.viewport().height()))
            step = max(
                24,
                min(round(line_height * 2), round(viewport_height * 0.12)),
            )
            delta = -step if key == Qt.Key.Key_Up else step
            self._scroll_smoothly(delta)
            return True
        return False

    def eventFilter(self, watched, event):
        if watched is self.reader.viewport() and event.type() == QEvent.Type.Wheel:
            self._stop_scroll_animation()
        return super().eventFilter(watched, event)

    def set_pure_mode(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if self._pure_mode == enabled:
            return
        self._pure_mode = enabled
        self.pure_button.setToolTip("退出纯净" if enabled else "切换纯净模式")
        self._apply_reading_chrome()
        self.pure_mode_changed.emit(enabled)

    def open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择小说文件",
            str(Path.home()),
            "Novels (*.txt *.md);;All Files (*)",
        )
        if path:
            self.load_path(Path(path))

    def load_path(self, path: Path) -> None:
        try:
            if path.stat().st_size > MAX_LOCAL_SIZE:
                raise ValueError("文件超过 20MB，暂时不支持加载")
            self._set_novel(path.stem, decode_bytes(path.read_bytes()), str(path))
        except (OSError, ValueError) as exc:
            self._set_status(str(exc), error=True)

    def _set_novel(self, title: str, text: str, source: str) -> None:
        chapters = split_chapters(text)
        if not chapters:
            self._set_status("没有读到正文内容", error=True)
            return
        self._chapters = chapters
        self.chapter_combo.blockSignals(True)
        self.chapter_combo.clear()
        self.chapter_combo.addItems([item[0] for item in chapters])
        self.chapter_combo.blockSignals(False)
        self._chapter_index = 0
        self.chapter_combo.setCurrentIndex(0)
        self._show_chapter(0)
        self.title_label.setText(title)
        self._set_status(f"{len(chapters)} 章 · {source}")

    def _on_chapter_selected(self, index: int) -> None:
        self._show_chapter(index)

    def _move_chapter(self, delta: int) -> None:
        target = self._chapter_index + delta
        if 0 <= target < len(self._chapters):
            self.chapter_combo.setCurrentIndex(target)

    def _show_chapter(self, index: int) -> None:
        if not 0 <= index < len(self._chapters):
            return
        self._chapter_index = index
        self._stop_scroll_animation()
        self.reader.setPlainText(self._chapters[index][1])
        self.reader.verticalScrollBar().setValue(0)
        self._scroll_target = 0
        self.prev_button.setEnabled(index > 0)
        self.next_button.setEnabled(index < len(self._chapters) - 1)
        self._update_progress()

    def _set_font_size(self, size: int) -> None:
        self._font_size = min(28, max(12, size))
        self.font_size_slider.blockSignals(True)
        self.font_size_slider.setValue(self._font_size)
        self.font_size_slider.blockSignals(False)
        self.font_size_value.setText(f"{self._font_size}px")
        self._apply_styles()

    def _apply_reading_chrome(self) -> None:
        pure = self._pure_mode
        self.head_bar.setVisible(not pure)
        self.footer_context_bar.setVisible(not pure)
        self.chapter_combo.setVisible(not pure)
        self.smaller_button.setVisible(not pure)
        self.larger_button.setVisible(not pure)
        self.progress_label.setVisible(not pure)
        self.font_row.setVisible(pure)
        self.footer_layout_set_stretch(1 if pure else 0)
        self.reader.setViewportMargins(46, 34, 40, 20 if pure else 0)
        self.prev_button.setText("")
        self.next_button.setText("")
        self.pure_button.setText("")
        self.prev_button.setToolTip("上一章")
        self.next_button.setToolTip("下一章")
        self.prev_button.setIcon(stroke_icon("chevron-left", self._theme.text, 20))
        self.next_button.setIcon(stroke_icon("chevron-right", self._theme.text, 20))
        self.pure_button.setIcon(stroke_icon("expand" if pure else "collapse", self._theme.text, 20))
        if pure:
            self.status_label.hide()
            action_row = self.footer_action_bar.layout()
            if action_row is not None:
                action_row.setContentsMargins(28, 7, 28, 5)
                action_row.setSpacing(14)
            context_row = self.footer_context_bar.layout()
            if context_row is not None:
                context_row.setContentsMargins(20, 6, 20, 0)
        else:
            action_row = self.footer_action_bar.layout()
            if action_row is not None:
                action_row.setContentsMargins(0, 0, 0, 0)
                action_row.setSpacing(6)
            context_row = self.footer_context_bar.layout()
            if context_row is not None:
                context_row.setContentsMargins(0, 0, 0, 0)
                context_row.setSpacing(8)
        self._apply_styles()

    def footer_layout_set_stretch(self, stretch: int) -> None:
        layout = self.footer_action_bar.layout()
        if layout is not None:
            layout.setStretchFactor(self.footer_stretch, stretch)

    def _update_progress(self) -> None:
        bar = self.reader.verticalScrollBar()
        percent = 100 if bar.maximum() == 0 else round(bar.value() * 100 / bar.maximum())
        self.progress_label.setText(f"{percent}%")

    def _scroll_smoothly(self, delta: int) -> None:
        bar = self.reader.verticalScrollBar()
        self._scroll_target = max(bar.minimum(), min(bar.maximum(), bar.value() + delta))
        if self._scroll_target == bar.value():
            self._stop_scroll_animation()
            return

        if self._scroll_animation is not None:
            self._scroll_animation.stop()
            self._scroll_animation.deleteLater()
            self._scroll_animation = None

        animation = QPropertyAnimation(bar, b"value", self)
        animation.setDuration(240)
        animation.setStartValue(bar.value())
        animation.setEndValue(self._scroll_target)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._scroll_animation = animation
        animation.finished.connect(self._stop_scroll_animation)
        animation.start()

    def _stop_scroll_animation(self) -> None:
        if self._scroll_animation is not None:
            self._scroll_animation.stop()
            self._scroll_animation.deleteLater()
            self._scroll_animation = None
        self._scroll_target = self.reader.verticalScrollBar().value()

    def _set_status(self, text: str, error: bool = False) -> None:
        self.status_label.setText(text)
        self.status_label.setVisible(bool(text))
        color = self._theme.danger if error else self._theme.text_secondary
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px;")

    def _apply_styles(self) -> None:
        self.title_label.setStyleSheet(
            f"color: {self._theme.text}; font-size: 13px; font-weight: 600;"
        )
        background = self._theme.content_bg if self._pure_mode else self._theme.surface
        border = "none" if self._pure_mode else f"1px solid {self._theme.border}"
        padding = "0" if self._pure_mode else "18px 20px"
        self.reader.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background: {background};
                color: {self._theme.text};
                selection-background-color: {self._theme.accent};
                selection-color: {self._theme.primary_text};
                border: {border};
                border-radius: {max(8, self._theme.chip_radius)}px;
                padding: {padding};
                font-size: {self._font_size}px;
                line-height: 165%;
            }}
            """
        )
        if self._pure_mode:
            self.font_size_label.setStyleSheet(
                f"color: {self._theme.text_secondary}; font-size: 12px; background: transparent;"
            )
            self.font_size_value.setStyleSheet(
                f"color: {self._theme.text}; font-size: 12px; background: transparent;"
            )
            self.font_size_slider.setStyleSheet(
                f"""
                QSlider {{
                    background: transparent;
                    height: 22px;
                }}
                QSlider::groove:horizontal {{
                    height: 2px;
                    background: {self._theme.separator};
                    border-radius: 1px;
                }}
                QSlider::handle:horizontal {{
                    width: 12px;
                    height: 12px;
                    margin: -5px 0;
                    border-radius: 6px;
                    background: {self._theme.accent};
                }}
                QSlider::sub-page:horizontal {{
                    height: 2px;
                    background: {self._theme.accent};
                    border-radius: 1px;
                }}
                """
            )
            self.footer_bar.setStyleSheet(
                "QWidget#novelFooter { background: transparent; }"
            )
            self.font_row.setStyleSheet(
                "QWidget#novelFontRow { background: transparent; }"
            )
            muted = self._theme.text
            accent = self._theme.accent
            for button in (self.prev_button, self.next_button):
                button.setCursor(Qt.PointingHandCursor)
                button.setStyleSheet(
                    f"""
                    QPushButton {{
                        background: transparent;
                        border: none;
                        border-bottom: 1px solid transparent;
                        border-radius: 0;
                        color: {muted};
                        padding: 4px;
                    }}
                    QPushButton:hover {{ color: {accent}; border-bottom-color: {accent}; }}
                    QPushButton:disabled {{ color: {self._theme.text_muted}; border-bottom-color: transparent; }}
                    """
                )
            self.pure_button.setCursor(Qt.PointingHandCursor)
            self.pure_button.setStyleSheet(
                f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-bottom: 1px solid transparent;
                    border-radius: 0;
                    color: {accent};
                    padding: 4px;
                }}
                QPushButton:hover {{ border-bottom-color: {accent}; }}
                """
            )
        else:
            self.footer_bar.setStyleSheet("")
            self.font_row.setStyleSheet("")
            for button in (
                self.prev_button,
                self.next_button,
                self.pure_button,
            ):
                button.setCursor(Qt.PointingHandCursor)
                button.setStyleSheet(
                    f"""
                    QPushButton {{
                        background: {self._theme.surface};
                        border: 1px solid {self._theme.border};
                        border-radius: {max(6, self._theme.chip_radius)}px;
                        color: {self._theme.text};
                        padding: 0;
                    }}
                    QPushButton:hover {{
                        color: {self._theme.accent};
                        border-color: {self._theme.accent};
                        background: {self._theme.hover};
                    }}
                    QPushButton:disabled {{ color: {self._theme.text_muted}; }}
                    """
                )
        if self.status_label.text():
            self._set_status(self.status_label.text())
