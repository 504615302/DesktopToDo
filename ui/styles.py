from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    label: str
    title: str
    placeholder: str
    font_family: str
    font_size: int
    radius: int
    chip_radius: int
    check_radius: int
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
    banner_bg: str
    banner_text: str
    primary_text: str = "#FFFFFF"


CUTE = Theme(
    name="cute",
    label="可爱风",
    title="今日待办 ♪",
    placeholder="✨  记一件小事，按 Enter 保存",
    font_family='"Microsoft YaHei UI", "Segoe UI", sans-serif',
    font_size=13,
    radius=22,
    chip_radius=16,
    check_radius=10,
    bg="#FFF4F7",
    surface="#FFFFFF",
    hover="#FFE8EF",
    border="#FFD0DC",
    text="#5C3344",
    text_secondary="#C56B84",
    text_muted="#E09AAD",
    accent="#FF7AA2",
    accent_soft="#FFD9E4",
    danger="#F0627A",
    success="#7BC67E",
    completed="#D4A5B3",
    shadow="#E8A0B4",
    input_bg="#FFFFFF",
    chip_active="#FFD6E3",
    banner_bg="#FF7AA2",
    banner_text="#FFFFFF",
    primary_text="#FFFFFF",
)

BUSINESS = Theme(
    name="business",
    label="商务风",
    title="工作待办",
    placeholder="添加工作事项，按 Enter 保存",
    font_family='"Microsoft YaHei UI", "Segoe UI", sans-serif',
    font_size=13,
    radius=8,
    chip_radius=4,
    check_radius=3,
    bg="#102033",
    surface="#173049",
    hover="#1E3C58",
    border="#2C4A66",
    text="#E7EEF6",
    text_secondary="#9BB0C4",
    text_muted="#6E8499",
    accent="#C9A227",
    accent_soft="#3A3318",
    danger="#E57373",
    success="#66BB6A",
    completed="#7A8B9C",
    shadow="#061018",
    input_bg="#0C1A2A",
    chip_active="#3A3318",
    banner_bg="#C9A227",
    banner_text="#1A1408",
    primary_text="#1A1408",
)

MINIMAL = Theme(
    name="minimal",
    label="简约风",
    title="待办",
    placeholder="添加任务，按 Enter 保存",
    font_family='"Microsoft YaHei UI", "Segoe UI", sans-serif',
    font_size=13,
    radius=14,
    chip_radius=8,
    check_radius=5,
    bg="#FAFAFA",
    surface="#FFFFFF",
    hover="#F0F0F0",
    border="#E6E6E6",
    text="#171717",
    text_secondary="#737373",
    text_muted="#A3A3A3",
    accent="#2563EB",
    accent_soft="#DBEAFE",
    danger="#DC2626",
    success="#16A34A",
    completed="#A3A3A3",
    shadow="#0F172A",
    input_bg="#FFFFFF",
    chip_active="#DBEAFE",
    banner_bg="#171717",
    banner_text="#FAFAFA",
    primary_text="#FFFFFF",
)

THEMES = {
    "cute": CUTE,
    "business": BUSINESS,
    "minimal": MINIMAL,
}

THEME_CHOICES = [(theme.label, theme.name) for theme in (CUTE, BUSINESS, MINIMAL)]

_LEGACY_THEME = {
    "light": "minimal",
    "dark": "business",
    "system": "minimal",
}


def resolve_theme(mode: str) -> Theme:
    key = _LEGACY_THEME.get(mode, mode)
    return THEMES.get(key, MINIMAL)


def build_stylesheet(theme: Theme) -> str:
    return f"""
    * {{
        font-family: {theme.font_family};
        font-size: {theme.font_size}px;
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
    QLineEdit, QPlainTextEdit, QComboBox, QDateTimeEdit {{
        background: {theme.input_bg};
        border: 1px solid {theme.border};
        border-radius: {max(6, theme.chip_radius)}px;
        padding: 8px 10px;
        color: {theme.text};
        selection-background-color: {theme.accent};
    }}
    QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QDateTimeEdit:focus {{
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
        border-radius: {max(6, theme.chip_radius)}px;
        padding: 8px 14px;
        color: {theme.text};
    }}
    QPushButton:hover {{
        background: {theme.hover};
    }}
    QPushButton#primaryButton {{
        background: {theme.accent};
        border: none;
        color: {theme.primary_text};
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
        border-radius: {theme.check_radius}px;
        border: 1px solid {theme.border};
        background: {theme.input_bg};
    }}
    QCheckBox::indicator:checked {{
        background: {theme.accent};
        border: 1px solid {theme.accent};
    }}
    QSlider::groove:horizontal {{
        height: 6px;
        background: {theme.border};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        width: 16px;
        height: 16px;
        margin: -6px 0;
        border-radius: 8px;
        background: {theme.accent};
    }}
    QSlider::sub-page:horizontal {{
        background: {theme.accent};
        border-radius: 3px;
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
