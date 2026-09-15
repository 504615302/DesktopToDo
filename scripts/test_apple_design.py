from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QWidget

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.nav_bar import NavBar
from ui.icons import asset_icon
from ui.page_utils import make_scroll
from ui.settings_dialog import SettingsDialog
from ui.styles import THEMES
from ui.title_bar import TitleBar
from model.settings import AppSettings


def test_themes_expose_shared_apple_surface_roles() -> None:
    for theme in THEMES.values():
        assert theme.chrome
        assert theme.content_bg
        assert theme.separator
        assert theme.focus_ring
        assert theme.nav_active


def test_primary_navigation_meets_pointer_target_size() -> None:
    app = QApplication.instance() or QApplication([])
    nav = NavBar(THEMES["minimal"])
    assert nav.objectName() == "primaryNavigation"
    assert nav.minimumHeight() >= 58
    assert all(button.minimumHeight() >= 50 for button in nav._buttons.values())
    expected = asset_icon("nav_today", 20).pixmap(20, 20).toImage()
    actual = nav._buttons["today"].icon().pixmap(20, 20).toImage()
    assert actual == expected
    nav.deleteLater()
    app.processEvents()


def test_title_bar_groups_product_and_window_actions() -> None:
    app = QApplication.instance() or QApplication([])
    title = TitleBar(THEMES["minimal"])
    assert title.objectName() == "titleBar"
    assert title.product_actions.objectName() == "productActions"
    assert title.window_actions.objectName() == "windowActions"
    assert title.minimumHeight() >= 48
    assert "border-left" in title.styleSheet()
    title.deleteLater()
    app.processEvents()


def test_scroll_content_does_not_fall_back_to_system_white() -> None:
    app = QApplication.instance() or QApplication([])
    host = QWidget()
    scroll = make_scroll(host)
    assert host.objectName() == "scrollContent"
    assert "transparent" in host.styleSheet()
    scroll.deleteLater()
    app.processEvents()


def test_settings_dialog_restyles_all_fixed_copy_for_preview_theme() -> None:
    app = QApplication.instance() or QApplication([])
    dialog = SettingsDialog(THEMES["minimal"], AppSettings(theme="minimal"))
    assert dialog._body.objectName() == "settingsBody"
    assert "transparent" in dialog._body.styleSheet()
    dialog.apply_theme(THEMES["tech"])
    assert dialog._theme is THEMES["tech"]
    assert all(THEMES["tech"].text_secondary in label.styleSheet() for label in dialog._hint_labels)
    dialog.deleteLater()
    app.processEvents()


if __name__ == "__main__":
    test_themes_expose_shared_apple_surface_roles()
    test_primary_navigation_meets_pointer_target_size()
    test_title_bar_groups_product_and_window_actions()
    test_scroll_content_does_not_fall_back_to_system_white()
    test_settings_dialog_restyles_all_fixed_copy_for_preview_theme()
    print("apple design ui ok")
