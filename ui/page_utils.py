from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from ui.styles import Theme


def section_label(text: str, theme: Theme) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(
        f"color: {theme.text_secondary}; font-size: 11px; font-weight: 600; "
        f"padding: 12px 8px 5px 8px; letter-spacing: 0.4px;"
    )
    return label


def empty_label(text: str, theme: Theme) -> QLabel:
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    label.setWordWrap(True)
    label.setMinimumHeight(132)
    label.setStyleSheet(
        f"background: {theme.surface}; color: {theme.text_secondary}; "
        f"border: 1px solid {theme.separator}; border-radius: 14px; padding: 32px 18px;"
    )
    return label


def make_scroll(host: QWidget) -> QScrollArea:
    host.setObjectName("scrollContent")
    host.setStyleSheet("QWidget#scrollContent { background: transparent; }")
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setFrameShape(QScrollArea.NoFrame)
    scroll.viewport().setAutoFillBackground(False)
    scroll.setWidget(host)
    return scroll


def clear_layout(layout: QVBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


def style_chip(button: QPushButton, theme: Theme, active: bool) -> None:
    bg = theme.nav_active if active else "transparent"
    color = theme.accent if active else theme.text_secondary
    button.setChecked(active)
    button.setStyleSheet(
        f"""
        QPushButton {{
            background: {bg};
            color: {color};
            border: 1px solid {theme.separator if active else 'transparent'};
            border-radius: {max(8, theme.chip_radius)}px;
            padding: 5px 10px;
            font-size: 12px;
        }}
        """
    )


def style_nav_button(button, theme: Theme, active: bool) -> None:
    bg = theme.nav_active if active else "transparent"
    color = theme.text if active else theme.text_secondary
    border = theme.separator if active else "transparent"
    radius = max(10, theme.chip_radius)
    button.setChecked(active)
    button.setStyleSheet(
        f"""
        QToolButton {{
            background: {bg};
            color: {color};
            border: 1px solid {border};
            border-radius: {radius}px;
            padding: 5px 2px 4px 2px;
            font-size: 12px;
            font-weight: {"600" if active else "500"};
        }}
        QToolButton:hover {{
            background: {theme.hover};
        }}
        QToolButton:pressed {{
            background: {theme.accent_soft};
        }}
        """
    )


def style_quick_add(row: QWidget, theme: Theme) -> None:
    row.setStyleSheet(
        f"""
        QWidget#quickAdd {{
            background: {theme.surface};
            border: 1px solid {theme.separator};
            border-radius: {max(12, theme.chip_radius)}px;
        }}
        QLineEdit {{
            background: transparent;
            border: none;
            padding: 0;
        }}
        """
    )
