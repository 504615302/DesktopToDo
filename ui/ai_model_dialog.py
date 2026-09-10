from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from model.report import AIModelConfig
from service.ai_service import AIClientError
from service.report_service import ReportService
from ui.framed_dialog import FramedDialog
from ui.styles import Theme


class AIModelDialog(FramedDialog):
    def __init__(self, theme: Theme, reports: ReportService, config: AIModelConfig | None = None, parent=None):
        super().__init__(theme, "编辑模型" if config else "新增模型", parent, width=440)
        self._reports = reports
        self._config = config or AIModelConfig(name="DeepSeek")
        self.name_edit = QLineEdit(self._config.name)
        self.base_edit = QLineEdit(self._config.api_base)
        self.base_edit.setPlaceholderText("https://api.deepseek.com/v1")
        self.model_edit = QLineEdit(self._config.model_name)
        self.model_edit.setPlaceholderText("deepseek-chat")
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.Password)
        self.token_edit.setPlaceholderText("已保存，留空则不修改" if self._config.encrypted_api_key else "sk-...")
        self.temp_edit = QLineEdit(str(self._config.temperature))
        self.tokens_edit = QLineEdit(str(self._config.max_tokens))
        self.status = QLabel()
        self.status.setWordWrap(True)

        for title, widget in (
            ("配置名称", self.name_edit),
            ("API Base", self.base_edit),
            ("Model", self.model_edit),
            ("Token", self.token_edit),
            ("Temperature", self.temp_edit),
            ("Max Tokens", self.tokens_edit),
        ):
            self.root.addWidget(self.caption(title))
            self.root.addWidget(widget)

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

    def _toggle_token(self) -> None:
        hidden = self.token_edit.echoMode() == QLineEdit.Password
        self.token_edit.setEchoMode(QLineEdit.Normal if hidden else QLineEdit.Password)

    def _filled(self) -> AIModelConfig:
        config = self._config
        config.name = self.name_edit.text().strip() or "未命名模型"
        config.provider = "openai-compatible"
        config.api_base = self.base_edit.text().strip()
        config.model_name = self.model_edit.text().strip()
        try:
            config.temperature = float(self.temp_edit.text().strip() or "0.3")
        except ValueError:
            config.temperature = 0.3
        try:
            config.max_tokens = int(self.tokens_edit.text().strip() or "4000")
        except ValueError:
            config.max_tokens = 4000
        return config

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
