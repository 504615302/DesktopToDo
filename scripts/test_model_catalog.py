from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_provider_catalog_defaults() -> None:
    from service.model_provider_catalog import PROVIDER_PRESETS, provider_by_id, normalize_api_base

    gemini = provider_by_id("google-gemini")
    assert gemini is not None
    assert normalize_api_base(gemini.api_base) == "https://generativelanguage.googleapis.com/v1beta/openai"
    assert {item.id for item in PROVIDER_PRESETS}.issuperset(
        {"openai", "deepseek", "qwen", "google-gemini", "kimi", "zhipu-glm", "openrouter", "siliconflow"}
    )


def test_catalog_matching_and_merge() -> None:
    from service.model_provider_catalog import CUSTOM_PROVIDER_ID, canonical_model_ids, match_provider, merged_model_ids

    assert match_provider("https://api.openai.com/v1/") == "openai"
    assert match_provider("https://example.test/v1") == CUSTOM_PROVIDER_ID
    assert merged_model_ids(["B", "a"], ["a", "c", " "]) == ["a", "B", "c"]
    assert canonical_model_ids("google-gemini", ["models/gemini-3.8-flash"]) == ["gemini-3.8-flash"]


def test_model_cache_roundtrip_and_isolation() -> None:
    from service.model_catalog_cache import ModelCatalogCache

    with TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        path = Path(temp_dir) / "models.json"
        cache = ModelCatalogCache(path)
        cache.save("openai", "https://api.openai.com/v1/", ["gpt-b", "gpt-a", "gpt-a"])
        assert cache.load("openai", "https://api.openai.com/v1") == ["gpt-a", "gpt-b"]
        assert cache.load("custom", "https://api.openai.com/v1") == []
        assert "sk-" not in path.read_text(encoding="utf-8")


def test_model_cache_ignores_corrupt_json() -> None:
    from service.model_catalog_cache import ModelCatalogCache

    with TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        path = Path(temp_dir) / "models.json"
        path.write_text("{broken", encoding="utf-8")
        assert ModelCatalogCache(path).load("openai", "https://api.openai.com/v1") == []


if __name__ == "__main__":
    test_provider_catalog_defaults()
    test_catalog_matching_and_merge()
    test_model_cache_roundtrip_and_isolation()
    test_model_cache_ignores_corrupt_json()
    print("model catalog ok")
