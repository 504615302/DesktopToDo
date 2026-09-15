# Model Provider Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add provider presets, an editable model selector, and authenticated online model-list refresh while preserving custom OpenAI-compatible configurations.

**Architecture:** A pure provider catalog owns preset metadata, a small JSON cache stores successful model discoveries without credentials, and `AIService` owns the compatible `GET /models` request. `AIModelDialog` composes those services, performs provider-to-endpoint linkage, and runs refresh work outside the UI thread.

**Tech Stack:** Python 3.14, PySide6, `urllib.request`, JSON, existing script-based smoke tests.

**Spec:** `docs/superpowers/specs/2026-09-15-model-provider-catalog-design.md`

## Global Constraints

- Support only OpenAI-compatible protocol; do not add Claude-native API behavior.
- API keys must never be written to catalog cache, logs, or error text.
- Existing saved `AIModelConfig` records must load without a database migration.
- The model field must remain freely editable after preset selection or online refresh.
- Online refresh failure must preserve built-in, cached, saved, and manually entered models.
- Utility-screen motion must be short, interruptible, and removable through the existing reduced-motion behavior.
- Preserve unrelated working-tree changes, especially `config/settings.json`.

---

### Task 1: Provider preset registry and URL normalization

**Files:**
- Create: `service/model_provider_catalog.py`
- Create: `scripts/test_model_catalog.py`

**Interfaces:**
- Produces: `ProviderPreset`, `PROVIDER_PRESETS`, `CUSTOM_PROVIDER_ID`, `provider_by_id(provider_id: str) -> ProviderPreset | None`, `match_provider(api_base: str) -> str`, `normalize_api_base(api_base: str) -> str`, `merged_model_ids(*groups: list[str]) -> list[str]`.

- [ ] **Step 1: Write the failing catalog tests**

```python
def test_provider_catalog_defaults() -> None:
    gemini = provider_by_id("google-gemini")
    assert gemini is not None
    assert normalize_api_base(gemini.api_base) == "https://generativelanguage.googleapis.com/v1beta/openai"
    assert "deepseek" in {item.id for item in PROVIDER_PRESETS}

def test_catalog_matching_and_merge() -> None:
    assert match_provider("https://api.openai.com/v1/") == "openai"
    assert match_provider("https://example.test/v1") == CUSTOM_PROVIDER_ID
    assert merged_model_ids(["B", "a"], ["a", "c", " "]) == ["a", "B", "c"]
```

- [ ] **Step 2: Run the test and verify RED**

Run: the project Python with `scripts/test_model_catalog.py`.

Expected: import failure for `service.model_provider_catalog`.

- [ ] **Step 3: Implement the immutable registry and helpers**

Create a frozen `ProviderPreset` dataclass with `id`, `name`, `api_base`, `models`, `supports_model_list`, and `api_key_required`. Populate OpenAI, Google Gemini, DeepSeek, Alibaba Qwen, Kimi, Zhipu GLM, OpenRouter, and SiliconFlow using verified OpenAI-compatible endpoints and a concise offline model set. Normalize only surrounding whitespace and trailing slashes; merge model IDs case-insensitively without losing their original spelling.

- [ ] **Step 4: Run the catalog test and verify GREEN**

Run: the project Python with `scripts/test_model_catalog.py`.

Expected: `model catalog ok`.

- [ ] **Step 5: Commit the focused change**

```powershell
git add -- service/model_provider_catalog.py scripts/test_model_catalog.py
git commit -m "feat: add model provider catalog"
```

### Task 2: Credential-free model catalog cache

**Files:**
- Create: `service/model_catalog_cache.py`
- Modify: `scripts/test_model_catalog.py`

**Interfaces:**
- Consumes: `normalize_api_base`, `merged_model_ids`.
- Produces: `ModelCatalogCache(path: Path)`, `load(provider_id: str, api_base: str) -> list[str]`, `save(provider_id: str, api_base: str, model_ids: list[str]) -> None`.

- [ ] **Step 1: Add failing cache round-trip and corruption tests**

```python
def test_model_cache_roundtrip_and_isolation(tmp: Path) -> None:
    cache = ModelCatalogCache(tmp / "models.json")
    cache.save("openai", "https://api.openai.com/v1/", ["gpt-b", "gpt-a", "gpt-a"])
    assert cache.load("openai", "https://api.openai.com/v1") == ["gpt-a", "gpt-b"]
    assert cache.load("custom", "https://api.openai.com/v1") == []
    assert "sk-" not in (tmp / "models.json").read_text(encoding="utf-8")

def test_model_cache_ignores_corrupt_json(tmp: Path) -> None:
    path = tmp / "models.json"
    path.write_text("{broken", encoding="utf-8")
    assert ModelCatalogCache(path).load("openai", "https://api.openai.com/v1") == []
```

- [ ] **Step 2: Run and verify RED**

Expected: import failure for `ModelCatalogCache`.

- [ ] **Step 3: Implement versioned atomic JSON persistence**

Use a versioned object with entries keyed by a SHA-256 digest of provider ID plus normalized Base URL. Store only `provider_id`, `api_base`, `models`, and an ISO timestamp. Write to a sibling temporary file and replace the destination. Treat missing, malformed, or unsupported-version data as an empty cache.

- [ ] **Step 4: Run and verify GREEN**

Expected: all catalog/cache tests pass.

- [ ] **Step 5: Commit the focused change**

```powershell
git add -- service/model_catalog_cache.py scripts/test_model_catalog.py
git commit -m "feat: cache discovered model lists"
```

### Task 3: Compatible model discovery service

**Files:**
- Modify: `service/ai_service.py`
- Modify: `scripts/test_services.py`

**Interfaces:**
- Consumes: `AIModelConfig`, `CredentialService`, `normalize_api_base`, `merged_model_ids`.
- Produces: `AIService.list_models(config: AIModelConfig, raw_key: str | None = None) -> list[str]` and `_get(url: str, api_key: str) -> dict`.

- [ ] **Step 1: Add failing response parsing and validation tests**

Add a tiny `StubAIService` overriding `_get` to return `{"data": [{"id": "z"}, {"id": "a"}, {"id": "a"}]}`. Assert `list_models` returns `["a", "z"]`, requests the normalized `/models` URL, uses the supplied key, rejects a blank Base URL, rejects a blank key, and raises `AIClientError("模型列表返回格式无法解析")` for malformed `data`.

- [ ] **Step 2: Run and verify RED**

Expected: `AIService` has no `list_models` method.

- [ ] **Step 3: Implement GET discovery and user-safe errors**

Use Bearer authentication and a finite timeout. Map 401/403 to a credential message, 404/405 to an unsupported-list message, URL failures to the existing network wording, empty compatible lists to a specific empty-list message, and all other HTTP failures through a bounded response excerpt. Never include the API key.

- [ ] **Step 4: Run and verify GREEN**

Run `scripts/test_services.py` and `scripts/test_model_catalog.py`.

Expected: both scripts pass.

- [ ] **Step 5: Commit the focused change**

```powershell
git add -- service/ai_service.py scripts/test_services.py
git commit -m "feat: discover provider models"
```

### Task 4: Provider-aware editable model form

**Files:**
- Modify: `ui/ai_model_dialog.py`
- Modify: `scripts/test_window.py`

**Interfaces:**
- Consumes: provider registry, `ModelCatalogCache`, `AIService.list_models`.
- Produces: `provider_combo: QComboBox`, `model_combo: QComboBox`, `refresh_button: QPushButton`, `_select_provider(provider_id: str)`, `_refresh_model_choices()`, `_start_model_refresh()`.

- [ ] **Step 1: Add failing dialog behavior tests**

Construct `AIModelDialog` with the temporary application context. Assert its model combo is editable; selecting Google Gemini fills the expected Base URL; typed `private-model` survives `_refresh_model_choices`; editing a legacy unknown URL selects “自定义”; and the refresh button text is `更新模型`.

- [ ] **Step 2: Run and verify RED**

Expected: missing `provider_combo`, `model_combo`, and `refresh_button` attributes.

- [ ] **Step 3: Replace the model line edit with a provider-aware editable combo**

Add the service-provider combo before Base URL. Add a horizontal model row containing the editable combo and 44-pixel-minimum refresh button. Infer the initial provider from the saved Base URL while preserving all legacy values. On provider changes, fill the preset Base URL and repopulate from built-ins plus cache plus the current text. `_filled()` must read `model_combo.currentText()` and store the selected provider ID, while unknown/legacy configurations use `openai-compatible` for persistence compatibility.

- [ ] **Step 4: Run and verify GREEN**

Run `scripts/test_window.py`.

Expected: window and dialog behavior tests pass.

- [ ] **Step 5: Commit the focused change**

```powershell
git add -- ui/ai_model_dialog.py scripts/test_window.py
git commit -m "feat: add provider-aware model picker"
```

### Task 5: Non-blocking refresh feedback and restrained animation

**Files:**
- Modify: `ui/ai_model_dialog.py`
- Modify: `ui/styles.py`
- Modify: `scripts/test_window.py`

**Interfaces:**
- Consumes: `AIService.list_models`, `ModelCatalogCache.save`, current theme semantic colors.
- Produces: a worker signal carrying either `list[str]` or a safe error, `_set_refresh_busy(bool)`, `_finish_model_refresh(list[str])`, `_fail_model_refresh(str)`.

- [ ] **Step 1: Add failing UI-state tests**

Inject a synchronous fake discovery callable for tests. Verify busy state disables only the refresh button, success caches and selects the typed model when still present, failure preserves all choices, and closing the dialog makes late completion harmless. Assert status labels use semantic object/property state rather than hard-coded per-theme foreground colors.

- [ ] **Step 2: Run and verify RED**

Expected: refresh state methods and injection seam do not exist.

- [ ] **Step 3: Implement a short-lived Qt worker and state feedback**

Run discovery away from the UI thread, hold worker/thread references until completion, and ignore callbacks after dialog destruction. Show delayed loading copy to avoid flicker. On success merge, cache, and show `已更新，共 N 个模型`; on failure show the classified error without a blocking message box. Apply a brief opacity emphasis only when reduced motion is not active; otherwise update text and semantic status color instantly.

- [ ] **Step 4: Run and verify GREEN**

Run `scripts/test_window.py` and `scripts/test_apple_design.py`.

Expected: both UI suites pass with no thread-destruction warnings.

- [ ] **Step 5: Commit the focused change**

```powershell
git add -- ui/ai_model_dialog.py ui/styles.py scripts/test_window.py
git commit -m "feat: refresh model list in settings"
```

### Task 6: Full regression and packaging safety

**Files:**
- Modify only if a failing regression requires a focused fix: `DesktopTODO.spec`, `service/__init__.py`, or the files above.

**Interfaces:**
- Consumes: all completed tasks.
- Produces: verified integrated application behavior.

- [ ] **Step 1: Run the complete automated suite**

Run in order: `scripts/test_model_catalog.py`, `scripts/test_services.py`, `scripts/test_apple_design.py`, and `scripts/test_window.py` with the project site-packages path.

Expected: all scripts print their success marker and exit zero.

- [ ] **Step 2: Perform a local offscreen interaction smoke test**

Open `AIModelDialog`, cycle every built-in provider, verify each Base URL is non-empty, type a custom model, switch to custom mode, and confirm `_filled()` preserves the text and normalized URL without making a real network call.

- [ ] **Step 3: Inspect the final diff and credential safety**

Run `git diff --check`, inspect only task-owned diffs, and search the new cache/catalog code for accidental key serialization. Confirm `config/settings.json` and unrelated Apple redesign edits were not overwritten.

- [ ] **Step 4: Commit any necessary integration-only adjustment**

```powershell
git add -- <only-the-files-required-by-the-regression-fix>
git commit -m "fix: complete model catalog integration"
```

- [ ] **Step 5: Record final verification evidence**

Report the exact passing scripts, built-in providers, refresh fallback behavior, and any provider whose official `/models` behavior could not be exercised without a real user key.
