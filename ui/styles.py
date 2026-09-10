from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    surface: str
    hover: str
    border: str
    text: str
    text_secondary: str
    text_muted: str
    accent: str
    accent_soft: str
    danger: str
    success: str
    completed: str
    shadow: str
    input_bg: str
    chip_active: str


DARK = Theme(
    name="dark",
    bg="#1C1C28",
    surface="#252536",
    hover="#2E2E44",
    border="#3A3A52",
    text="#F4F4F5",
    text_secondary="#A1A1AA",
    text_muted="#71717A",
    accent="#818CF8",
    accent_soft="#312E81",
    danger="#F87171",
    success="#34D399",
    completed="#71717A",
    shadow="#000000",
    input_bg="#16161F",
    chip_active="#3730A3",
)

LIGHT = Theme(
    name="light",
    bg="#F7F7FA",
    surface="#FFFFFF",
    hover="#EEF0F6",
    border="#E4E4E7",
    text="#18181B",
    text_secondary="#52525B",
    text_muted="#A1A1AA",
    accent="#4F46E5",
    accent_soft="#E0E7FF",
    danger="#DC2626",
    success="#059669",
    completed="#A1A1AA",
    shadow="#0F172A",
    input_bg="#FFFFFF",
    chip_active="#EEF2FF",
)


def is_windows_dark() -> bool:
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return int(value) == 0
    except OSError:
        return True


def resolve_theme(mode: str) -> Theme:
    if mode == "light":
        return LIGHT
    if mode == "dark":
        return DARK
    return DARK if is_windows_dark() else LIGHT


def build_stylesheet(theme: Theme) -> str:
    return f"""
    * {{
        font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
        font-size: 13px;
        color: {theme.text};
    }}
    QDialog, QMessageBox {{
        background: {theme.bg};
        color: {theme.text};
    }}
    QLabel {{
        background: transparent;
        color: {theme.text};
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 4px 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {theme.border};
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {theme.text_muted};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        height: 0;
        background: none;
    }}
    QLineEdit, QPlainTextEdit, QComboBox {{
        background: {theme.input_bg};
        border: 1px solid {theme.border};
        border-radius: 8px;
        padding: 8px 10px;
        color: {theme.text};
        selection-background-color: {theme.accent};
    }}
    QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
        border: 1px solid {theme.accent};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background: {theme.surface};
        border: 1px solid {theme.border};
        selection-background-color: {theme.hover};
        color: {theme.text};
        outline: none;
    }}
    QPushButton {{
        background: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: 8px;
        padding: 8px 14px;
        color: {theme.text};
    }}
    QPushButton:hover {{
        background: {theme.hover};
    }}
    QPushButton#primaryButton {{
        background: {theme.accent};
        border: none;
        color: #FFFFFF;
        font-weight: 600;
    }}
    QPushButton#primaryButton:hover {{
        background: {theme.accent};
    }}
    QPushButton#dangerButton {{
        color: {theme.danger};
        border: 1px solid {theme.danger};
    }}
    QCheckBox {{
        spacing: 8px;
        color: {theme.text};
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid {theme.border};
        background: {theme.input_bg};
    }}
    QCheckBox::indicator:checked {{
        background: {theme.accent};
        border: 1px solid {theme.accent};
    }}
    QMenu {{
        background: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: 8px;
        padding: 6px;
        color: {theme.text};
    }}
    QMenu::item {{
        padding: 6px 18px;
        border-radius: 6px;
    }}
    QMenu::item:selected {{
        background: {theme.hover};
    }}
    QToolTip {{
        background: {theme.surface};
        color: {theme.text};
        border: 1px solid {theme.border};
        padding: 4px 8px;
    }}
    """
