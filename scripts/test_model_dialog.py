from __future__ import annotations

import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.db import Database
from main import build_context
from service.model_catalog_cache import ModelCatalogCache
from ui.ai_model_dialog import AIModelDialog
from ui.styles import resolve_theme


def test_model_dialog() -> None:
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    with TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        tmp = Path(temp_dir)
        database = Database(tmp / "todo.db")
        try:
            context = build_context(database, tmp / "settings.json")
            dialog = AIModelDialog(resolve_theme("minimal"), context.reports)
            assert dialog.model_combo.isEditable()
            assert dialog.refresh_button.text() == "更新模型"
            dialog._select_provider("google-gemini")
            assert dialog.base_edit.text() == "https://generativelanguage.googleapis.com/v1beta/openai"
            dialog.model_combo.setCurrentText("private-model")
            dialog._refresh_model_choices()
            assert dialog.model_combo.currentText() == "private-model"
            dialog.base_edit.setText("https://example.test/v1")
            dialog._sync_provider_from_base()
            assert dialog.provider_combo.currentData() == "custom"
            dialog._cache = ModelCatalogCache(tmp / "models.json")
            dialog._select_provider("openai")
            dialog.model_combo.setCurrentText("private-model")
            dialog._finish_model_refresh(["gpt-test", "gpt-test"])
            assert dialog.refresh_button.isEnabled()
            assert dialog.model_combo.currentText() == "private-model"
            assert dialog._cache.load("openai", "https://api.openai.com/v1") == ["gpt-test"]
            choices_before = [dialog.model_combo.itemText(index) for index in range(dialog.model_combo.count())]
            dialog._fail_model_refresh("Token 无效")
            assert [dialog.model_combo.itemText(index) for index in range(dialog.model_combo.count())] == choices_before
            context.reports.ai.list_models = lambda config, raw_key: ["refreshed-model"]
            dialog.token_edit.setText("test-key")
            dialog._start_model_refresh()
            deadline = time.monotonic() + 2
            while dialog._refresh_thread is not None and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.01)
            assert dialog._refresh_thread is None
            assert "refreshed-model" in [dialog.model_combo.itemText(index) for index in range(dialog.model_combo.count())]
            dialog.close()
        finally:
            database.close()


if __name__ == "__main__":
    test_model_dialog()
    print("model dialog ok")
