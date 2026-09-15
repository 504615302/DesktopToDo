from __future__ import annotations

from PySide6.QtCore import QObject, QSignalBlocker, QThread, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app_paths import config_dir
from model.report import AIModelConfig
from service.ai_service import AIClientError
from service.model_catalog_cache import ModelCatalogCache
from service.model_provider_catalog import (
    CUSTOM_PROVIDER_ID,
    PROVIDER_PRESETS,
    canonical_model_ids,
    match_provider,
    merged_model_ids,
    normalize_api_base,
    provider_by_id,
)
from service.report_service import ReportService
from ui.framed_dialog import FramedDialog
from ui.styles import Theme


class _ModelRefreshWorker(QObject):
    succeeded = Signal(list)
    failed = Signal(str)

    def __init__(self, service, config: AIModelConfig, raw_key: str | None):
        super().__init__()
        self._service = service
        self._config = config
        self._raw_key = raw_key

    def run(self) -> None:
        try:
            self.succeeded.emit(self._service.list_models(self._config, self._raw_key))
        except AIClientError as exc:
            self.failed.emit(str(exc))
        except Exception:
            self.failed.emit("模型更新失败，请稍后重试")


class AIModelDialog(FramedDialog):
    def __init__(self, theme: Theme, reports: ReportService, config: AIModelConfig | None = None, parent=None):
        super().__init__(theme, "编辑模型" if config else "新增模型", parent, width=440)
        self._reports = reports
        self._config = config or AIModelConfig(name="DeepSeek")
        self._cache = ModelCatalogCache(config_dir() / "model_catalog.json")
        self._refresh_thread: QThread | None = None
        self._refresh_worker: _ModelRefreshWorker | None = None
        self._refresh_provider_id = CUSTOM_PROVIDER_ID
        self._refresh_api_base = ""
        self.name_edit = QLineEdit(self._config.name)
        self.provider_combo = QComboBox()
        for preset in PROVIDER_PRESETS:
            self.provider_combo.addItem(preset.name, preset.id)
        self.provider_combo.addItem("自定义", CUSTOM_PROVIDER_ID)
        self.base_edit = QLineEdit(self._config.api_base)
        self.base_edit.setPlaceholderText("https://api.deepseek.com/v1")
        self.model_combo = QComboBox()
        self.model_combo.setObjectName("modelCombo")
        self.model_combo.setEditable(True)
        self.model_combo.setInsertPolicy(QComboBox.NoInsert)
        self.model_combo.setMaxVisibleItems(9)
        self.model_combo.setMinimumHeight(40)
        self.model_combo.view().setObjectName("modelComboMenu")
        self.model_combo.view().setMinimumWidth(320)
        self.model_combo.setCurrentText(self._config.model_name)
        self.model_combo.setPlaceholderText("选择或输入模型名称")
        self.refresh_button = QPushButton("更新模型")
        self.refresh_button.setMinimumWidth(88)
        self.refresh_button.setMinimumHeight(36)
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.Password)
        self.token_edit.setPlaceholderText("已保存，留空则不修改" if self._config.encrypted_api_key else "sk-...")
        self.temp_edit = QLineEdit(str(self._config.temperature))
        self.tokens_edit = QLineEdit(str(self._config.max_tokens))
        self.status = QLabel()
        self.status.setWordWrap(True)

        for title, widget in (
            ("配置名称", self.name_edit),
            ("服务商", self.provider_combo),
            ("API Base", self.base_edit),
            ("Token", self.token_edit),
            ("Temperature", self.temp_edit),
            ("Max Tokens", self.tokens_edit),
        ):
            self.root.addWidget(self.caption(title))
            self.root.addWidget(widget)

        self.root.insertWidget(7, self.caption("Model"))
        model_row = QHBoxLayout()
        model_row.setSpacing(8)
        model_row.addWidget(self.model_combo, 1)
        model_row.addWidget(self.refresh_button)
        self.root.insertLayout(8, model_row)

        show = QPushButton("显示 / 隐藏 Token")
        show.setFixedHeight(30)
        show.clicked.connect(self._toggle_token)
        self.root.addWidget(show)
        self.root.addWidget(self.status)

        buttons = QHBoxLayout()
        test = QPushButton("测试连接")
        save = QPushButton("保存")
        save.setObjectName("primaryButton")
        test.setFixedHeight(34)
        save.setFixedHeight(34)
        test.clicked.connect(self._test)
        save.clicked.connect(self._save)
        buttons.addWidget(test)
        buttons.addWidget(save)
        self.root.addLayout(buttons)

        self.provider_combo.currentIndexChanged.connect(self._provider_changed)
        self.base_edit.editingFinished.connect(self._sync_provider_from_base)
        self.refresh_button.clicked.connect(self._start_model_refresh)
        self._sync_provider_from_base()
        self._refresh_model_choices()

    def _toggle_token(self) -> None:
        hidden = self.token_edit.echoMode() == QLineEdit.Password
        self.token_edit.setEchoMode(QLineEdit.Normal if hidden else QLineEdit.Password)

    def _filled(self) -> AIModelConfig:
        config = self._config
        config.name = self.name_edit.text().strip() or "未命名模型"
        provider_id = self.provider_combo.currentData()
        config.provider = provider_id if provider_id != CUSTOM_PROVIDER_ID else "openai-compatible"
        config.api_base = normalize_api_base(self.base_edit.text())
        config.model_name = self.model_combo.currentText().strip()
        try:
            config.temperature = float(self.temp_edit.text().strip() or "0.3")
        except ValueError:
            config.temperature = 0.3
        try:
            config.max_tokens = int(self.tokens_edit.text().strip() or "4000")
        except ValueError:
            config.max_tokens = 4000
        return config

    def _provider_changed(self) -> None:
        provider_id = self.provider_combo.currentData()
        preset = provider_by_id(provider_id)
        if preset is not None:
            self.base_edit.setText(normalize_api_base(preset.api_base))
        self._refresh_model_choices()

    def _select_provider(self, provider_id: str) -> None:
        index = self.provider_combo.findData(provider_id)
        if index >= 0:
            self.provider_combo.setCurrentIndex(index)

    def _sync_provider_from_base(self) -> None:
        provider_id = match_provider(self.base_edit.text())
        index = self.provider_combo.findData(provider_id)
        if index >= 0:
            blocker = QSignalBlocker(self.provider_combo)
            self.provider_combo.setCurrentIndex(index)
            del blocker
        self._refresh_model_choices()

    def _refresh_model_choices(self) -> None:
        current = self.model_combo.currentText().strip()
        provider_id = self.provider_combo.currentData()
        preset = provider_by_id(provider_id)
        built_in = list(preset.models) if preset is not None else []
        cached = self._cache.load(provider_id, self.base_edit.text())
        choices = merged_model_ids(built_in, canonical_model_ids(provider_id, cached), [current])
        blocker = QSignalBlocker(self.model_combo)
        self.model_combo.clear()
        self.model_combo.addItems(choices)
        self.model_combo.setCurrentText(current)
        del blocker

    def _start_model_refresh(self) -> None:
        if self._refresh_thread is not None:
            return
        config = self._filled()
        raw_key = self.token_edit.text().strip() or None
        if raw_key is None and not config.encrypted_api_key:
            self._fail_model_refresh("请先填写 Token")
            return
        self._set_refresh_busy(True)
        provider_id = self.provider_combo.currentData()
        api_base = self.base_edit.text()
        thread = QThread(self)
        worker = _ModelRefreshWorker(self._reports.ai, config, raw_key)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(self._on_discovery_succeeded)
        worker.failed.connect(self._fail_model_refresh)
        worker.succeeded.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._refresh_finished)
        self._refresh_thread = thread
        self._refresh_worker = worker
        self._refresh_provider_id = provider_id
        self._refresh_api_base = api_base
        thread.start()

    def _set_refresh_busy(self, busy: bool) -> None:
        self.refresh_button.setEnabled(not busy)
        self.refresh_button.setText("正在更新…" if busy else "更新模型")
        if busy:
            self.status.setText("正在从服务商获取模型列表…")

    def _refresh_finished(self) -> None:
        self._refresh_thread = None
        self._refresh_worker = None
        self._set_refresh_busy(False)

    def _on_discovery_succeeded(self, model_ids: list[str]) -> None:
        self._finish_model_refresh(model_ids, self._refresh_provider_id, self._refresh_api_base)

    def _finish_model_refresh(
        self,
        model_ids: list[str],
        provider_id: str | None = None,
        api_base: str | None = None,
    ) -> None:
        provider_id = provider_id or self.provider_combo.currentData()
        api_base = api_base or self.base_edit.text()
        model_ids = canonical_model_ids(provider_id, model_ids)
        self._cache.save(provider_id, api_base, model_ids)
        self._refresh_model_choices()
        self.status.setText(f"已更新，共 {len(merged_model_ids(model_ids))} 个模型，可在模型下拉框中选择")
        self._set_refresh_busy(False)

    def _fail_model_refresh(self, message: str) -> None:
        self.status.setText(message)
        self._set_refresh_busy(False)

    def _test(self) -> None:
        config = self._filled()
        raw = self.token_edit.text().strip() or None
        try:
            message = self._reports.ai.test_connection(config, raw)
            self.status.setText("✓ " + message)
        except AIClientError as exc:
            self.status.setText(str(exc))
            QMessageBox.warning(self, "连接失败", str(exc))

    def _save(self) -> None:
        config = self._filled()
        raw = self.token_edit.text().strip() or None
        if config.id is None and not raw:
            QMessageBox.information(self, "提示", "请填写 Token")
            return
        self._reports.save_model(config, raw)
        self.accept()


class AIModelListDialog(FramedDialog):
    def __init__(self, theme: Theme, reports: ReportService, parent=None):
        super().__init__(theme, "AI 模型", parent, width=440)
        self._theme = theme
        self._reports = reports
        self.box = QVBoxLayout()
        self.root.addLayout(self.box)
        add = QPushButton("新增模型")
        add.setObjectName("primaryButton")
        add.clicked.connect(lambda: self._edit(None))
        self.root.addWidget(add)
        self._reload()

    def _reload(self) -> None:
        while self.box.count():
            item = self.box.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        models = self._reports.models()
        if not models:
            empty = QLabel("还没有模型配置")
            empty.setStyleSheet(f"color: {self._theme.text_muted};")
            self.box.addWidget(empty)
            return
        for config in models:
            row = QWidget()
            layout = QHBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)
            label = QLabel(f"{config.name}\n{config.model_name}  {config.masked_key()}")
            label.setWordWrap(True)
            edit = QPushButton("编辑")
            delete = QPushButton("删除")
            delete.setObjectName("dangerButton")
            edit.clicked.connect(lambda _=False, item=config: self._edit(item))
            delete.clicked.connect(lambda _=False, item=config: self._delete(item))
            layout.addWidget(label, 1)
            layout.addWidget(edit)
            layout.addWidget(delete)
            self.box.addWidget(row)

    def _edit(self, config: AIModelConfig | None = None) -> None:
        dialog = AIModelDialog(self._theme, self._reports, config, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self._reload()

    def _delete(self, config: AIModelConfig) -> None:
        if QMessageBox.question(self, "删除模型", f"确认删除 {config.name}？") != QMessageBox.StandardButton.Yes:
            return
        if config.id is not None:
            self._reports.delete_model(config.id)
        self._reload()
