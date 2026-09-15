"""Built-in OpenAI-compatible model provider metadata."""

from __future__ import annotations

from dataclasses import dataclass

CUSTOM_PROVIDER_ID = "custom"


@dataclass(frozen=True)
class ProviderPreset:
    id: str
    name: str
    api_base: str
    models: tuple[str, ...]
    supports_model_list: bool = True
    api_key_required: bool = True


PROVIDER_PRESETS: tuple[ProviderPreset, ...] = (
    ProviderPreset("openai", "OpenAI", "https://api.openai.com/v1", ("gpt-6-astra", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna")),
    ProviderPreset("google-gemini", "Google Gemini", "https://generativelanguage.googleapis.com/v1beta/openai/", ("gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.5-pro")),
    ProviderPreset("deepseek", "DeepSeek", "https://api.deepseek.com/v1", ("deepseek-chat", "deepseek-reasoner")),
    ProviderPreset("qwen", "通义千问", "https://dashscope.aliyuncs.com/compatible-mode/v1", ("qwen-plus", "qwen-max", "qwen3-coder-plus")),
    ProviderPreset("kimi", "Kimi", "https://api.moonshot.cn/v1", ("kimi-k2.5", "kimi-k2-turbo-preview", "moonshot-v1-8k")),
    ProviderPreset("zhipu-glm", "智谱 GLM", "https://open.bigmodel.cn/api/paas/v4", ("glm-4.7", "glm-4.5-air", "glm-4-flash")),
    ProviderPreset("openrouter", "OpenRouter", "https://openrouter.ai/api/v1", ("openai/gpt-5.6", "google/gemini-3-flash-preview", "deepseek/deepseek-chat")),
    ProviderPreset("siliconflow", "SiliconFlow", "https://api.siliconflow.cn/v1", ("deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1", "Qwen/Qwen3-32B")),
)


def normalize_api_base(api_base: str) -> str:
    return (api_base or "").strip().rstrip("/")


def provider_by_id(provider_id: str) -> ProviderPreset | None:
    return next((item for item in PROVIDER_PRESETS if item.id == provider_id), None)


def match_provider(api_base: str) -> str:
    normalized = normalize_api_base(api_base)
    for preset in PROVIDER_PRESETS:
        if normalize_api_base(preset.api_base) == normalized:
            return preset.id
    return CUSTOM_PROVIDER_ID


def merged_model_ids(*groups: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for group in groups:
        for value in group:
            model_id = (value or "").strip()
            key = model_id.casefold()
            if model_id and key not in seen:
                seen.add(key)
                result.append(model_id)
    return sorted(result, key=str.casefold)


def canonical_model_ids(provider_id: str, model_ids: list[str]) -> list[str]:
    if provider_id == "google-gemini":
        model_ids = [model_id.removeprefix("models/") for model_id in model_ids]
    return merged_model_ids(model_ids)
