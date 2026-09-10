from __future__ import annotations

from calendar import Calendar
from datetime import datetime, timedelta

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ui.icons import stroke_icon
from ui.styles import Theme

WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]
QUICK_DATES = [("今天", 0), ("明天", 1), ("后天", 2)]
QUICK_TIMES = ["09:00", "12:00", "14:00", "18:00", "21:00"]


class IconButton(QToolButton):
    def __init__(self, kind: str, color: str, tooltip: str = "", size: int = 32, icon_size: int = 16, parent=None):
        super().__init__(parent)
        self._kind = kind
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setAutoRaise(True)
        self.setFixedSize(size, size)
        self.setIconSize(QSize(icon_size, icon_size))
        self.set_color(color)
        self.setStyleSheet(
            f"""
            QToolButton {{
                border: none;
                border-radius: {size // 2}px;
                background: transparent;
                padding: 0;
            }}
            QToolButton:hover {{
                background: rgba(127, 127, 127, 36);
            }}
            QToolButton:pressed {{
                background: rgba(127, 127, 127, 56);
            }}
            """
        )

    def set_color(self, color: str) -> None:
        self.setIcon(stroke_icon(self._kind, color, 18))

    def set_kind(self, kind: str, color: str) -> None:
        self._kind = kind
        self.set_color(color)


class Chip(QPushButton):
    def __init__(self, text: str, theme: Theme, parent=None):
        super().__init__(text, parent)
        self._theme = theme
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(30)
        self._apply()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._apply()

    def _apply(self) -> None:
        theme = self._theme
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {theme.surface};
                color: {theme.text_secondary};
                border: 1px solid {theme.border};
                border-radius: {theme.chip_radius}px;
                padding: 0 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {theme.hover};
            }}
            QPushButton:checked {{
                background: {theme.accent};
                color: {theme.primary_text};
                border: 1px solid {theme.accent};
                font-weight: 600;
            }}
            """
        )


class DateTimePicker(QWidget):
    changed = Signal()

    def __init__(self, theme: Theme, value: datetime | None = None, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._value = value or (datetime.now().replace(second=0, microsecond=0) + timedelta(hours=1))
        self._cursor = self._value.replace(day=1)
        self._day_buttons: list[QPushButton] = []
        self._build()
        self._refresh()

    def value(self) -> datetime:
        return self._value

    def set_value(self, value: datetime) -> None:
        self._value = value.replace(second=0, microsecond=0)
        self._cursor = self._value.replace(day=1)
        self._refresh()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.setObjectName("dateTimePicker")
        self.setAttribute(Qt.WA_StyledBackground, True)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.prev_btn = IconButton("chevron-left", self._theme.text_secondary, "上个月")
        self.next_btn = IconButton("chevron-right", self._theme.text_secondary, "下个月")
        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignCenter)
        self.prev_btn.clicked.connect(self._prev_month)
        self.next_btn.clicked.connect(self._next_month)
        header.addWidget(self.prev_btn)
        header.addWidget(self.month_label, 1)
        header.addWidget(self.next_btn)
        layout.addLayout(header)

        week = QHBoxLayout()
        week.setSpacing(0)
        for name in WEEKDAYS:
            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedHeight(22)
            week.addWidget(label)
        layout.addLayout(week)
        self._week_labels = [week.itemAt(i).widget() for i in range(week.count())]

        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setContentsMargins(0, 0, 0, 0)
        for index in range(42):
            button = QPushButton()
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedSize(38, 32)
            button.setFocusPolicy(Qt.NoFocus)
            button.clicked.connect(lambda _=False, slot=index: self._pick_slot(slot))
            self._day_buttons.append(button)
            grid.addWidget(button, index // 7, index % 7)
        layout.addLayout(grid)

        quick = QHBoxLayout()
        quick.setSpacing(6)
        self._date_chips: list[Chip] = []
        for text, offset in QUICK_DATES:
            chip = Chip(text, self._theme)
            chip.clicked.connect(lambda _=False, days=offset: self._set_offset_days(days))
            self._date_chips.append(chip)
            quick.addWidget(chip)
        quick.addStretch()
        layout.addLayout(quick)

        time_row = QHBoxLayout()
        clock = QLabel()
        clock.setPixmap(stroke_icon("clock", self._theme.text_secondary, 16).pixmap(16, 16))
        self._clock_icon = clock
        time_row.addWidget(clock)
        time_row.addWidget(self._time_label("时间"))
        time_row.addStretch()
        self.hour_down = IconButton("chevron-down", self._theme.text_secondary, "小时-1", 28, 14)
        self.hour_up = IconButton("chevron-up", self._theme.text_secondary, "小时+1", 28, 14)
        self.minute_down = IconButton("chevron-down", self._theme.text_secondary, "分钟-5", 28, 14)
        self.minute_up = IconButton("chevron-up", self._theme.text_secondary, "分钟+5", 28, 14)
        self.hour_label = QLabel()
        self.minute_label = QLabel()
        self.colon = QLabel(":")
        self.colon.setAlignment(Qt.AlignCenter)
        self.hour_label.setAlignment(Qt.AlignCenter)
        self.minute_label.setAlignment(Qt.AlignCenter)
        self.hour_label.setFixedSize(52, 36)
        self.minute_label.setFixedSize(52, 36)
        self.colon.setFixedWidth(14)
        self.hour_label.setAttribute(Qt.WA_StyledBackground, True)
        self.minute_label.setAttribute(Qt.WA_StyledBackground, True)
        self.hour_up.clicked.connect(lambda: self._nudge_time(hours=1))
        self.hour_down.clicked.connect(lambda: self._nudge_time(hours=-1))
        self.minute_up.clicked.connect(lambda: self._nudge_time(minutes=5))
        self.minute_down.clicked.connect(lambda: self._nudge_time(minutes=-5))
        hour_box = QVBoxLayout()
        hour_box.setSpacing(0)
        hour_box.addWidget(self.hour_up, 0, Qt.AlignCenter)
        hour_box.addWidget(self.hour_label)
        hour_box.addWidget(self.hour_down, 0, Qt.AlignCenter)
        minute_box = QVBoxLayout()
        minute_box.setSpacing(0)
        minute_box.addWidget(self.minute_up, 0, Qt.AlignCenter)
        minute_box.addWidget(self.minute_label)
        minute_box.addWidget(self.minute_down, 0, Qt.AlignCenter)
        time_row.addLayout(hour_box)
        time_row.addWidget(self.colon)
        time_row.addLayout(minute_box)
        layout.addLayout(time_row)

        chips = QHBoxLayout()
        chips.setSpacing(6)
        self._time_chips: list[Chip] = []
        for text in QUICK_TIMES:
            chip = Chip(text, self._theme)
            chip.clicked.connect(lambda _=False, value=text: self._set_time_text(value))
            self._time_chips.append(chip)
            chips.addWidget(chip)
        chips.addStretch()
        layout.addLayout(chips)
        self._apply_chrome()

    def _time_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"color: {self._theme.text_secondary}; font-size: 12px;")
        return label

    def _apply_chrome(self) -> None:
        theme = self._theme
        self.setStyleSheet(
            f"""
            QWidget#dateTimePicker {{
                background: {theme.surface};
                border: 1px solid {theme.border};
                border-radius: {max(12, theme.radius - 4)}px;
            }}
            """
        )
        self.month_label.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {theme.text};")
        for label in self._week_labels:
            label.setStyleSheet(f"color: {theme.text_secondary}; font-size: 12px; font-weight: 600;")
        digit = f"""
            background: {theme.input_bg};
            border: 1px solid {theme.border};
            border-radius: {max(8, theme.chip_radius)}px;
            font-size: 22px;
            font-weight: 700;
            color: {theme.text};
            font-family: Consolas, "Cascadia Mono", "Microsoft YaHei UI", sans-serif;
        """
        self.hour_label.setStyleSheet(digit)
        self.minute_label.setStyleSheet(digit)
        self.colon.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {theme.text};")
        self.prev_btn.set_color(theme.text_secondary)
        self.next_btn.set_color(theme.text_secondary)
        self.hour_up.set_color(theme.text_secondary)
        self.hour_down.set_color(theme.text_secondary)
        self.minute_up.set_color(theme.text_secondary)
        self.minute_down.set_color(theme.text_secondary)
        self._clock_icon.setPixmap(stroke_icon("clock", theme.text_secondary, 16).pixmap(16, 16))
        for chip in self._date_chips + self._time_chips:
            chip.apply_theme(theme)

    def _days(self) -> list[datetime | None]:
        year, month = self._cursor.year, self._cursor.month
        cal = Calendar(firstweekday=0)
        days: list[datetime | None] = [
            datetime(day.year, day.month, day.day) for day in cal.itermonthdates(year, month)
        ]
        while len(days) < 42:
            days.append(None)
        return days[:42]

    def _refresh(self) -> None:
        theme = self._theme
        self.month_label.setText(f"{self._cursor.year} 年 {self._cursor.month} 月")
        today = datetime.now().date()
        selected = self._value.date()
        for button, day in zip(self._day_buttons, self._days()):
            if day is None:
                button.setText("")
                button.setEnabled(False)
                button.setStyleSheet("QPushButton { background: transparent; border: none; padding: 0; color: transparent; }")
                continue
            button.setEnabled(True)
            in_month = day.month == self._cursor.month
            is_selected = day.date() == selected
            is_today = day.date() == today
            button.setText(str(day.day))
            if is_selected:
                bg, fg, border, weight = theme.accent, theme.primary_text, theme.accent, 700
            elif is_today:
                bg, fg, border, weight = theme.accent_soft, theme.accent, theme.accent, 700
            elif in_month:
                bg, fg, border, weight = theme.input_bg, theme.text, theme.border, 600
            else:
                bg, fg, border, weight = "transparent", theme.text_secondary, "transparent", 500
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background: {bg};
                    color: {fg};
                    border: 1px solid {border};
                    border-radius: {max(8, theme.chip_radius)}px;
                    font-size: 13px;
                    font-weight: {weight};
                    padding: 0;
                    min-width: 38px;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background: {theme.hover if not is_selected else theme.accent};
                    color: {theme.primary_text if is_selected else theme.text};
                }}
                """
            )
        self.hour_label.setText(f"{self._value.hour:02d}")
        self.minute_label.setText(f"{self._value.minute:02d}")
        for chip, (_, offset) in zip(self._date_chips, QUICK_DATES):
            chip.setChecked(selected == (datetime.now() + timedelta(days=offset)).date())
        current = self._value.strftime("%H:%M")
        for chip in self._time_chips:
            chip.setChecked(chip.text() == current)

    def _pick_slot(self, index: int) -> None:
        day = self._days()[index]
        if day is None:
            return
        self._cursor = day.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self._replace(year=day.year, month=day.month, day=day.day)

    def _replace(self, **kwargs) -> None:
        self._value = self._value.replace(**kwargs)
        self._refresh()
        self.changed.emit()

    def _set_offset_days(self, days: int) -> None:
        target = datetime.now() + timedelta(days=days)
        self._cursor = target.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self._replace(year=target.year, month=target.month, day=target.day)

    def _set_time_text(self, text: str) -> None:
        hour, minute = (int(part) for part in text.split(":"))
        self._replace(hour=hour, minute=minute)

    def _nudge_time(self, hours: int = 0, minutes: int = 0) -> None:
        self._value = self._value + timedelta(hours=hours, minutes=minutes)
        self._cursor = self._value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self._refresh()
        self.changed.emit()

    def _prev_month(self) -> None:
        month = self._cursor.month - 1
        year = self._cursor.year
        if month < 1:
            month = 12
            year -= 1
        self._cursor = self._cursor.replace(year=year, month=month, day=1)
        self._refresh()

    def _next_month(self) -> None:
        month = self._cursor.month + 1
        year = self._cursor.year
        if month > 12:
            month = 1
            year += 1
        self._cursor = self._cursor.replace(year=year, month=month, day=1)
        self._refresh()
