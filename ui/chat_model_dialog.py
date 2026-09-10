from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QSlider

from model.report import AIModelConfig
from service.report_service import ReportService
from ui.ai_model_dialog import AIModelListDialog
from ui.framed_dialog import FramedDialog
from ui.styles import Theme


class ChatModelDialog(FramedDialog):
    def __init__(
        self,
        theme: Theme,
        reports: ReportService,
        model_id: int | None,
        temperature: float,
        max_tokens: int,
        parent=None,
    ):
        super().__init__(theme, "问答模型", parent, width=400)
        self._theme = theme
        self._reports = reports
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.root.addWidget(self.caption("模型"))
        self.model_combo = QComboBox()
        self.model_combo.setMinimumHeight(34)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        self.root.addWidget(self.model_combo)

        temp_head = QHBoxLayout()
        temp_head.addWidget(self.caption("温度 Temperature"))
        self.temp_value = QLabel()
        self.temp_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        temp_head.addWidget(self.temp_value)
        self.root.addLayout(temp_head)
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(0, 200)
        self.temp_slider.valueChanged.connect(self._on_temp_changed)
        self.root.addWidget(self.temp_slider)
        hint = QLabel("越低越稳定，越高越有创意")
        hint.setStyleSheet(f"color: {theme.text_muted}; font-size: 11px;")
        self.root.addWidget(hint)

        token_head = QHBoxLayout()
        token_head.addWidget(self.caption("回复长度 Max Tokens"))
        self.token_value = QLabel()
        self.token_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        token_head.addWidget(self.token_value)
        self.root.addLayout(token_head)
        self.token_slider = QSlider(Qt.Horizontal)
        self.token_slider.setRange(256, 8192)
        self.token_slider.valueChanged.connect(self._on_token_changed)
        self.root.addWidget(self.token_slider)

        buttons = QHBoxLayout()
        manage = QPushButton("管理模型")
        manage.setFixedHeight(34)
        manage.clicked.connect(self._manage_models)
        apply = QPushButton("使用")
        apply.setObjectName("primaryButton")
        apply.setFixedHeight(34)
        apply.clicked.connect(self._apply)
        buttons.addWidget(manage)
        buttons.addWidget(apply)
        self.root.addLayout(buttons)

        self._reload_models(select_id=model_id)
        self._set_temp(temperature)
        self._set_tokens(max_tokens)

    def _models(self) -> list[AIModelConfig]:
        return self._reports.models()

    def _reload_models(self, select_id: int | None) -> None:
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        selected = 0
        for index, config in enumerate(self._models()):
            self.model_combo.addItem(f"{config.name}  ·  {config.model_name}", config.id)
            if select_id is not None and config.id == select_id:
                selected = index
        self.model_combo.setCurrentIndex(selected)
        self.model_combo.blockSignals(False)
        self.model_combo.setEnabled(self.model_combo.count() > 0)

    def _current_config(self) -> AIModelConfig | None:
        model_id = self.model_combo.currentData()
        return next((item for item in self._models() if item.id == model_id), None)

    def _on_model_changed(self) -> None:
        config = self._current_config()
        if config is None:
            return
        self._set_temp(config.temperature)
        self._set_tokens(config.max_tokens)

    def _set_temp(self, value: float) -> None:
        clamped = min(2.0, max(0.0, float(value)))
        self.temp_slider.blockSignals(True)
        self.temp_slider.setValue(int(round(clamped * 100)))
        self.temp_slider.blockSignals(False)
        self._on_temp_changed(self.temp_slider.value())

    def _set_tokens(self, value: int) -> None:
        clamped = min(8192, max(256, int(value)))
        self.token_slider.blockSignals(True)
        self.token_slider.setValue(clamped)
        self.token_slider.blockSignals(False)
        self._on_token_changed(self.token_slider.value())

    def _on_temp_changed(self, value: int) -> None:
        self.temperature = value / 100.0
        self.temp_value.setText(f"{self.temperature:.2f}")

    def _on_token_changed(self, value: int) -> None:
        self.max_tokens = int(value)
        self.token_value.setText(str(self.max_tokens))

    def _manage_models(self) -> None:
        current = self.model_combo.currentData()
        AIModelListDialog(self._theme, self._reports, self).exec()
        self._reload_models(select_id=current)

    def _apply(self) -> None:
        if self.model_combo.count() == 0:
            self._manage_models()
            if self.model_combo.count() == 0:
                return
        self.model_id = self.model_combo.currentData()
        self.temperature = self.temp_slider.value() / 100.0
        self.max_tokens = self.token_slider.value()
        self.accept()
