# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from ui.entertainment_panel import EntertainmentPanel
from ui.styles import resolve_theme


class EntertainmentKeyboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_vertical_keys_adjust_volume(self) -> None:
        panel = EntertainmentPanel(resolve_theme("minimal"))
        panel.audio_output.setVolume(0.5)
        up = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
        down = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)

        self.assertTrue(panel.handle_key(up))
        self.assertAlmostEqual(panel.audio_output.volume(), 0.55)
        self.assertTrue(panel.handle_key(down))
        self.assertAlmostEqual(panel.audio_output.volume(), 0.5)


if __name__ == "__main__":
    unittest.main()
