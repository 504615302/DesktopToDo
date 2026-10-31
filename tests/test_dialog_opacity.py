from __future__ import annotations

import unittest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ui.framed_dialog import FramedDialog
from ui.settings_dialog import SettingsDialog
from ui.styles import resolve_theme
from model.settings import AppSettings


class DialogOpacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_framed_dialog_is_opaque(self) -> None:
        theme = resolve_theme("latest")
        dialog = FramedDialog(theme, "不透明弹框", None, width=360)
        dialog.resize(360, 220)

        self.assertFalse(dialog.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))
        image = dialog.grab().toImage()
        expected = theme.bg.lstrip("#")
        red, green, blue = int(expected[0:2], 16), int(expected[2:4], 16), int(expected[4:6], 16)
        for position in ((0, 0), (image.width() - 1, 0), (0, image.height() - 1), (image.width() - 1, image.height() - 1)):
            color = image.pixelColor(*position)
            self.assertLessEqual(abs(color.red() - red), 2)
            self.assertLessEqual(abs(color.green() - green), 2)
            self.assertLessEqual(abs(color.blue() - blue), 2)
        dialog.deleteLater()

    def test_settings_dialog_is_opaque(self) -> None:
        theme = resolve_theme("meadow")
        dialog = SettingsDialog(theme, AppSettings(theme="meadow"))

        self.assertFalse(dialog.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))
        self.assertIn(theme.bg, dialog.styleSheet())
        dialog.deleteLater()


if __name__ == "__main__":
    unittest.main()
