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
    chrome: str
    content_bg: str
    separator: str
    focus_ring: str
    nav_active: str
    primary_text: str = "#FFFFFF"


CUTE = Theme(
    name="cute",
    label="可爱风",
    title="桌面代办 ♪",
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
    chrome="#FFF9FB",
    content_bg="#FFF4F7",
    separator="#F3DCE4",
    focus_ring="#FF7AA2",
    nav_active="#FFFFFF",
    primary_text="#FFFFFF",
)

BUSINESS = Theme(
    name="business",
    label="商务风",
    title="桌面代办",
    placeholder="添加工作事项，按 Enter 保存",
    font_family='"Microsoft YaHei UI", "Segoe UI", sans-serif',
    font_size=13,
    radius=8,
    chip_radius=4,
    check_radius=3,
    bg="#1E3346",
    surface="#263D52",
    hover="#2F4B63",
    border="#3E5C74",
    text="#E7EEF4",
    text_secondary="#B7C6D4",
    text_muted="#A3B2C0",
    accent="#C4B47A",
    accent_soft="#2A3F53",
    danger="#DE8C8C",
    success="#73BE79",
    completed="#9AA8B4",
    shadow="#152232",
    input_bg="#1B3043",
    chip_active="#314D64",
    banner_bg="#2A3F53",
    banner_text="#D2C496",
    chrome="#22384B",
    content_bg="#1E3346",
    separator="#355169",
    focus_ring="#C4B47A",
    nav_active="#314D64",
    primary_text="#1A1C14",
)

MINIMAL = Theme(
    name="minimal",
    label="简约风",
    title="桌面代办",
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
    chrome="#F7F7F8",
    content_bg="#FAFAFA",
    separator="#E8E8EA",
    focus_ring="#2563EB",
    nav_active="#FFFFFF",
    primary_text="#FFFFFF",
)

TECH = Theme(
    name="tech",
    label="科技风",
    title="桌面代办",
    placeholder="> 输入任务，按 Enter 保存",
    font_family='"Microsoft YaHei UI", "Segoe UI", sans-serif',
    font_size=13,
    radius=10,
    chip_radius=6,
    check_radius=4,
    bg="#070B14",
    surface="#101826",
    hover="#162033",
    border="#1C3D4A",
    text="#D7F6FF",
    text_secondary="#9AD0DE",
    text_muted="#8AADB8",
    accent="#2EE6D6",
    accent_soft="#0C2A30",
    danger="#FF5D7A",
    success="#3DFF9A",
    completed="#8AA2AC",
    shadow="#02040A",
    input_bg="#0A111C",
    chip_active="#12363C",
    banner_bg="#2EE6D6",
    banner_text="#041016",
    chrome="#0C1320",
    content_bg="#070B14",
    separator="#18313D",
    focus_ring="#2EE6D6",
    nav_active="#132331",
    primary_text="#041016",
)

THEMES = {
    "cute": CUTE,
    "business": BUSINESS,
    "minimal": MINIMAL,
    "tech": TECH,
}

THEME_CHOICES = [(theme.label, theme.name) for theme in (CUTE, BUSINESS, MINIMAL, TECH)]

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
    QLineEdit, QPlainTextEdit, QComboBox, QDateTimeEdit, QDateEdit {{
        background: {theme.input_bg};
        border: 1px solid {theme.border};
        border-radius: {max(6, theme.chip_radius)}px;
        padding: 8px 12px;
        color: {theme.text};
        selection-background-color: {theme.accent};
    }}
    QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QDateTimeEdit:focus, QDateEdit:focus {{
        border: 2px solid {theme.focus_ring};
    }}
    QLineEdit::placeholder, QPlainTextEdit::placeholder {{
        color: {theme.text_secondary};
    }}
    QComboBox::drop-down {{
        border: none;
        border-left: 1px solid {theme.separator};
        width: 32px;
    }}
    QComboBox QAbstractItemView {{
        background: {theme.surface};
        border: 1px solid {theme.border};
        selection-background-color: {theme.hover};
        color: {theme.text};
        outline: none;
        padding: 6px;
    }}
    QComboBox QAbstractItemView::item {{
        min-height: 34px;
        padding: 0 12px;
        border-radius: {max(6, theme.chip_radius - 2)}px;
    }}
    QComboBox QAbstractItemView::item:hover {{
        background: {theme.hover};
    }}
    QComboBox QAbstractItemView::item:selected {{
        background: {theme.accent};
        color: {theme.primary_text};
    }}
    QComboBox#modelCombo {{
        padding: 9px 38px 9px 12px;
        border-radius: {max(8, theme.chip_radius)}px;
        font-weight: 500;
    }}
    QComboBox#modelCombo::drop-down {{
        width: 34px;
        border-left: 1px solid {theme.separator};
    }}
    QComboBox#modelCombo QAbstractItemView#modelComboMenu {{
        padding: 6px;
        border: 1px solid {theme.border};
        border-radius: {max(8, theme.chip_radius)}px;
        background: {theme.surface};
        selection-background-color: {theme.accent};
        selection-color: {theme.primary_text};
    }}
    QComboBox#modelCombo QAbstractItemView#modelComboMenu::item {{
        min-height: 34px;
        padding: 0 12px;
        border-radius: {max(6, theme.chip_radius - 2)}px;
        color: {theme.text};
    }}
    QComboBox#modelCombo QAbstractItemView#modelComboMenu::item:hover {{
        background: {theme.hover};
    }}
    QComboBox#modelCombo QAbstractItemView#modelComboMenu::item:selected {{
        background: {theme.accent};
        color: {theme.primary_text};
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
    QPushButton:focus, QToolButton:focus {{
        border: 2px solid {theme.focus_ring};
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
