from __future__ import annotations

import unittest

from model.settings import AppSettings
from ui.styles import MEADOW, THEME_CHOICES, resolve_theme


class ThemeSettingsTests(unittest.TestCase):
    def test_meadow_theme_roundtrip(self) -> None:
        settings = AppSettings.from_dict({"theme": "meadow"})
        self.assertEqual(settings.theme, "meadow")
        self.assertEqual(resolve_theme(settings.theme), MEADOW)
        self.assertIn(("自然·松烟", "meadow"), THEME_CHOICES)


if __name__ == "__main__":
    unittest.main()
