from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from ui.styles import Theme


def section_label(text: str, theme: Theme) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(
        f"color: {theme.text_secondary}; font-size: 12px; font-weight: 600; padding: 8px 8px 4px 8px;"
    )
    return label


def empty_label(text: str, theme: Theme) -> QLabel:
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    label.setWordWrap(True)
    label.setStyleSheet(f"color: {theme.text_secondary}; padding: 28px 8px;")
    return label


def make_scroll(host: QWidget) -> QScrollArea:
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
    bg = theme.chip_active if active else theme.surface
    color = theme.accent if active else theme.text_secondary
    button.setChecked(active)
    button.setStyleSheet(
        f"""
        QPushButton {{
            background: {bg};
            color: {color};
            border: 1px solid {theme.border};
            border-radius: {theme.chip_radius}px;
            padding: 4px 9px;
            font-size: 12px;
        }}
        """
    )


def style_nav_button(button, theme: Theme, active: bool) -> None:
    bg = theme.chip_active if active else "transparent"
    color = theme.text if active else theme.text_secondary
    border = theme.accent if active else "transparent"
    radius = max(10, theme.chip_radius)
    button.setChecked(active)
    button.setStyleSheet(
        f"""
        QToolButton {{
            background: {bg};
            color: {color};
            border: 1px solid {border};
            border-radius: {radius}px;
            padding: 6px 2px 5px 2px;
            font-size: 12px;
            font-weight: {"600" if active else "500"};
        }}
        QToolButton:hover {{
            background: {theme.hover};
        }}
        """
    )


def style_quick_add(row: QWidget, theme: Theme) -> None:
    row.setStyleSheet(
        f"""
        QWidget#quickAdd {{
            background: {theme.input_bg};
            border: 1px solid {theme.border};
            border-radius: {max(10, theme.chip_radius)}px;
        }}
        QLineEdit {{
            background: transparent;
            border: none;
            padding: 0;
        }}
        """
    )
