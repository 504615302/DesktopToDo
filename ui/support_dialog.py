from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from app_paths import pay_path
from ui.framed_dialog import FramedDialog
from ui.styles import Theme

BLURB = {
    "cute": "如果这个小工具帮到你了，扫码请作者喝杯奶茶 ♪",
    "business": "如果桌面代办对你有帮助，欢迎支持作者。",
    "minimal": "如果这个小工具帮到你了，欢迎扫码支持。",
    "tech": "如果这个工具对你有用，欢迎支持作者。",
}


class SupportAuthorDialog(FramedDialog):
    def __init__(self, theme: Theme, parent=None):
        super().__init__(theme, "支持作者", parent, width=500)
        intro = QLabel(BLURB.get(theme.name, BLURB["minimal"]))
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color: {theme.text_secondary}; font-size: 13px;")
        self.root.addWidget(intro)

        codes = QHBoxLayout()
        codes.setSpacing(12)
        codes.addWidget(self._pay_card("微信", "wechat.png"), 1)
        codes.addWidget(self._pay_card("支付宝", "alipay.png"), 1)
        self.root.addLayout(codes)

        thanks = QLabel("谢谢你的支持")
        thanks.setAlignment(Qt.AlignCenter)
        thanks.setStyleSheet(f"color: {theme.text_muted}; font-size: 12px;")
        self.root.addWidget(thanks)

    def _pay_card(self, title: str, filename: str) -> QWidget:
        theme = self._theme
        card = QWidget()
        card.setObjectName("payCard")
        card.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        heading = QLabel(title)
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet(f"color: {theme.text}; font-size: 13px; font-weight: 600;")

        image = QLabel()
        image.setAlignment(Qt.AlignCenter)
        image.setMinimumSize(180, 260)
        image.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        pixmap = QPixmap(str(pay_path(filename)))
        if pixmap.isNull():
            image.setText("收款码即将放入")
            image.setWordWrap(True)
            image.setStyleSheet(f"color: {theme.text_muted}; font-size: 12px;")
        else:
            image.setPixmap(
                pixmap.scaled(180, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

        layout.addWidget(heading)
        layout.addWidget(image, 1)
        radius = max(10, theme.chip_radius)
        card.setStyleSheet(
            f"""
            QWidget#payCard {{
                background: {theme.surface};
                border: 1px solid {theme.border};
                border-radius: {radius}px;
            }}
            """
        )
        return card
