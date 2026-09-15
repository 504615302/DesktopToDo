"""Local cache for successful model-discovery responses without credentials."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from service.model_provider_catalog import merged_model_ids, normalize_api_base

_VERSION = 1


class ModelCatalogCache:
    def __init__(self, path: Path):
        self._path = path

    def load(self, provider_id: str, api_base: str) -> list[str]:
        body = self._read()
        key = self._key(provider_id, api_base)
        entry = body.get("entries", {}).get(key)
        if not isinstance(entry, dict):
            return []
        models = entry.get("models")
        if not isinstance(models, list) or not all(isinstance(item, str) for item in models):
            return []
        return merged_model_ids(models)

    def save(self, provider_id: str, api_base: str, model_ids: list[str]) -> None:
        normalized = normalize_api_base(api_base)
        if not normalized:
            return
        body = self._read()
        entries = body.setdefault("entries", {})
        entries[self._key(provider_id, normalized)] = {
            "provider_id": provider_id,
            "api_base": normalized,
            "models": merged_model_ids(model_ids),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._path.with_suffix(self._path.suffix + ".tmp")
        temporary.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, self._path)

    def _read(self) -> dict:
        try:
            value = json.loads(self._path.read_text(encoding="utf-8"))
            if value.get("version") != _VERSION or not isinstance(value.get("entries"), dict):
                return self._empty()
            return value
        except (OSError, json.JSONDecodeError, AttributeError):
            return self._empty()

    @staticmethod
    def _empty() -> dict:
        return {"version": _VERSION, "entries": {}}

    @staticmethod
    def _key(provider_id: str, api_base: str) -> str:
        raw = f"{provider_id}\n{normalize_api_base(api_base)}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
