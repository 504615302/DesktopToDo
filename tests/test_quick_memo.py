from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog

from ui.dialogs.quick_input_dialog import QuickInputDialog
from ui.main_window import MainWindow
from ui.styles import resolve_theme


class QuickInputDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.dialog = QuickInputDialog(resolve_theme("minimal"), "快速记录", "输入备忘内容")
        self.dialog.show()
        self.dialog.edit.setFocus()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.dialog.close()
        self.dialog.deleteLater()
        self.app.processEvents()

    def test_enter_inserts_newline_without_saving(self) -> None:
        self.dialog.edit.setPlainText("第一行")
        cursor = self.dialog.edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.dialog.edit.setTextCursor(cursor)
        QTest.keyClick(self.dialog.edit, Qt.Key_Return)
        self.dialog.edit.insertPlainText("第二行")

        self.assertEqual(self.dialog.result(), QDialog.DialogCode.Rejected)
        self.assertEqual(self.dialog.text(), "第一行\n第二行")

    def test_shift_enter_saves_non_empty_note(self) -> None:
        self.dialog.edit.setPlainText("快速记录")
        QTest.keyClick(self.dialog.edit, Qt.Key_Return, Qt.ShiftModifier)

        self.assertEqual(self.dialog.result(), QDialog.DialogCode.Accepted)

    def test_shift_enter_does_not_save_empty_note(self) -> None:
        QTest.keyClick(self.dialog.edit, Qt.Key_Return, Qt.ShiftModifier)

        self.assertEqual(self.dialog.result(), QDialog.DialogCode.Rejected)

    def test_escape_cancels_note(self) -> None:
        self.dialog.edit.setPlainText("不保存这条记录")
        QTest.keyClick(self.dialog.edit, Qt.Key_Escape)

        self.assertEqual(self.dialog.result(), QDialog.DialogCode.Rejected)


class _MemoStore:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add_memo(self, text: str) -> None:
        self.items.append(text)


class _Context:
    def __init__(self) -> None:
        self.memos = _MemoStore()


class _QuickMemoWindow:
    quick_memo_from_tray = MainWindow.quick_memo_from_tray

    def __init__(self) -> None:
        self.theme = resolve_theme("minimal")
        self.ctx = _Context()
        self.shown = False
        self.page = "today"
        self.reload_count = 0

    def show_from_tray(self) -> None:
        self.shown = True

    def set_page(self, page: str) -> None:
        self.page = page

    def reload_all(self) -> None:
        self.reload_count += 1


class QuickMemoWindowTests(unittest.TestCase):
    def test_quick_memo_keeps_main_window_hidden_and_saves(self) -> None:
        window = _QuickMemoWindow()

        with patch("ui.main_window.QuickInputDialog") as dialog_type:
            dialog_type.DialogCode = QDialog.DialogCode
            dialog = dialog_type.return_value
            dialog.exec.return_value = QDialog.DialogCode.Accepted
            dialog.text.return_value = "不打断当前工作"
            window.quick_memo_from_tray()

        self.assertFalse(window.shown)
        self.assertEqual(window.ctx.memos.items, ["不打断当前工作"])
        self.assertEqual(window.page, "today")
        self.assertEqual(window.reload_count, 1)


if __name__ == "__main__":
    unittest.main()
