# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from ui.novel_panel import NovelPanel, decode_bytes, split_chapters
from ui.styles import resolve_theme


class NovelPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_split_chapters(self) -> None:
        text = "第一章 出发\n甲\n\n第二章 抵达\n乙"
        chapters = split_chapters(text)

        self.assertEqual([item[0] for item in chapters], ["第一章 出发", "第二章 抵达"])
        self.assertIn("甲", chapters[0][1])
        self.assertIn("乙", chapters[1][1])

    def test_decode_bytes_gbk(self) -> None:
        self.assertEqual(decode_bytes("小说".encode("gb18030")), "小说")

    def test_local_file_reader(self) -> None:
        with TemporaryDirectory() as folder:
            path = Path(folder) / "novel.txt"
            path.write_text("第一章 出发\n正文一\n\n第二章 抵达\n正文二", encoding="utf-8")
            panel = NovelPanel(resolve_theme("minimal"))
            panel.load_path(path)

            self.assertEqual(panel.chapter_combo.count(), 2)
            self.assertTrue(panel.reader.toPlainText().startswith("第一章"))
            panel.next_button.click()
            self.assertTrue(panel.reader.toPlainText().startswith("第二章"))
            panel.larger_button.click()
            self.assertEqual(panel._font_size, 18)

    def test_pure_mode_keeps_basic_controls(self) -> None:
        panel = NovelPanel(resolve_theme("minimal"))
        panel._set_novel(
            "测试小说",
            "第一章 出发\n正文一\n\n第二章 抵达\n正文二",
            "test",
        )

        panel.set_pure_mode(True)

        self.assertTrue(panel.is_pure_mode())
        self.assertFalse(panel.head_bar.isVisible())
        self.assertFalse(panel.chapter_combo.isVisible())
        self.assertFalse(panel.smaller_button.isVisible())
        self.assertFalse(panel.larger_button.isVisible())
        self.assertFalse(panel.prev_button.isHidden())
        self.assertFalse(panel.next_button.isHidden())
        self.assertFalse(panel.font_row.isHidden())
        self.assertEqual(panel.font_size_slider.value(), panel._font_size)
        self.assertEqual(panel.prev_button.text(), "")
        self.assertEqual(panel.next_button.text(), "")
        self.assertEqual(panel.pure_button.text(), "")
        self.assertFalse(panel.prev_button.icon().isNull())
        self.assertFalse(panel.next_button.icon().isNull())
        self.assertFalse(panel.pure_button.icon().isNull())
        self.assertEqual(panel.pure_button.toolTip(), "退出纯净")
        self.assertIn("transparent", panel.prev_button.styleSheet())
        self.assertNotIn("border-top", panel.footer_bar.styleSheet())
        self.assertTrue(panel.font_size_slider.width() >= 120)
        self.assertGreaterEqual(panel.font_row.y(), panel.footer_action_bar.y())

        panel.font_size_slider.setValue(20)
        assert panel._font_size == 20
        self.assertEqual(panel.font_size_value.text(), "20px")

        panel.set_pure_mode(False)

        self.assertFalse(panel.is_pure_mode())
        self.assertFalse(panel.head_bar.isHidden())
        self.assertFalse(panel.chapter_combo.isHidden())
        self.assertTrue(panel.font_row.isHidden())
        self.assertEqual(panel.prev_button.text(), "")
        self.assertEqual(panel.next_button.text(), "")
        self.assertEqual(panel.pure_button.text(), "")
        self.assertEqual(panel.prev_button.toolTip(), "上一章")
        self.assertEqual(panel.next_button.toolTip(), "下一章")
        self.assertEqual(panel.pure_button.toolTip(), "切换纯净模式")

    def test_arrow_keys_switch_chapters_and_scroll(self) -> None:
        panel = NovelPanel(resolve_theme("minimal"))
        long_text = "第一章 出发\n" + ("这一行用于产生垂直滚动。\n" * 200) + "\n\n第二章 抵达\n正文"
        panel._set_novel("键盘测试", long_text, "test")
        panel.resize(360, 520)
        panel.show()

        right = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier)
        left = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Left, Qt.KeyboardModifier.NoModifier)
        down = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
        up = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
        repeated_down = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Down,
            Qt.KeyboardModifier.NoModifier,
            "",
            True,
            1,
        )

        self.assertTrue(panel.handle_key(right))
        self.assertEqual(panel._chapter_index, 1)
        self.assertTrue(panel.handle_key(left))
        self.assertEqual(panel._chapter_index, 0)

        QApplication.processEvents()
        bar = panel.reader.verticalScrollBar()
        self.assertGreater(bar.maximum(), 0)

        self.assertTrue(panel.handle_key(down))
        self.assertIsNotNone(panel._scroll_animation)
        self.assertGreater(panel._scroll_target, 0)
        line_height = panel.reader.fontMetrics().lineSpacing()
        maximum_step = max(24, min(round(line_height * 2), round(panel.reader.viewport().height() * 0.12)))
        self.assertLessEqual(panel._scroll_target, maximum_step + 1)
        self.assertEqual(panel._scroll_animation.duration(), 240)

        target_before_repeat = panel._scroll_target
        self.assertTrue(panel.handle_key(repeated_down))
        self.assertEqual(panel._scroll_target, target_before_repeat)

        panel._scroll_animation.setCurrentTime(panel._scroll_animation.duration())
        QApplication.processEvents()
        self.assertGreater(bar.value(), 0)

        value = bar.value()
        progress_at_first_stop = panel.progress_label.text()
        self.assertTrue(panel.handle_key(down))
        self.assertGreater(panel._scroll_target, value)
        panel._scroll_animation.setCurrentTime(panel._scroll_animation.duration())
        QApplication.processEvents()
        self.assertGreater(bar.value(), value)
        self.assertNotEqual(panel.progress_label.text(), progress_at_first_stop)

        value = bar.value()
        self.assertTrue(panel.handle_key(up))
        self.assertLess(panel._scroll_target, value)
        panel._scroll_animation.setCurrentTime(panel._scroll_animation.duration())
        QApplication.processEvents()
        self.assertLess(bar.value(), value)

    def test_normal_footer_separates_chapter_context_from_actions(self) -> None:
        panel = NovelPanel(resolve_theme("minimal"))
        panel._set_novel(
            "布局测试",
            "第一章 布局\n正文\n\n第二章 间距\n正文",
            "test",
        )
        panel.resize(308, 520)
        panel.show()
        QApplication.processEvents()

        self.assertTrue(panel.footer_context_bar.isVisible())
        self.assertLess(
            panel.footer_context_bar.y() + panel.footer_context_bar.height(),
            panel.footer_action_bar.y() + 2,
        )
        self.assertLessEqual(
            panel.chapter_combo.y() + panel.chapter_combo.height(),
            panel.footer_context_bar.height() + 2,
        )
        self.assertLessEqual(
            panel.prev_button.y() + panel.prev_button.height(),
            panel.footer_action_bar.height() + 2,
        )
        action_widgets = (
            panel.prev_button,
            panel.next_button,
            panel.smaller_button,
            panel.larger_button,
            panel.pure_button,
        )
        for widget in action_widgets:
            self.assertLessEqual(widget.x() + widget.width(), panel.footer_action_bar.width() + 1)

        panel.set_pure_mode(True)
        QApplication.processEvents()
        self.assertTrue(panel.footer_context_bar.isHidden())
        self.assertFalse(panel.prev_button.isHidden())
        self.assertFalse(panel.pure_button.isHidden())


if __name__ == "__main__":
    unittest.main()
