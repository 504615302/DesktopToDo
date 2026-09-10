from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from model.report import AIModelConfig
from service.credential_service import CredentialService

SYSTEM_PROMPT = """你是一名专业的工作周报整理助手。

请根据用户提供的已完成任务、工作备忘、未完成任务及补充信息生成工作周报。

要求：
1. 严格使用用户提供的数据
2. 不编造工作内容
3. 合并重复事项
4. 突出实际完成成果
5. 使用专业、简洁的工作语言
6. 下周计划优先从未完成任务中提取
7. 严格遵循用户指定的周报模板
8. 不改变用户模板章节结构
"""

QA_SYSTEM_PROMPT = """你是桌面代办里的问答助手。
根据用户问题简洁作答，适合在小窗口里阅读。
若提供了待办或备忘上下文，必须依据这些事实，不要编造不存在的任务或记录。
可以用短条目列出建议，避免空话套话。
"""

_COMPLETION_TOKEN_MARKERS = (
    "o1",
    "o3",
    "o4",
    "gpt-5",
    "gpt-4.1",
    "chatgpt-",
)


class AIClientError(RuntimeError):
    pass


def prefers_completion_tokens(model_name: str) -> bool:
    name = (model_name or "").lower()
    return any(name.startswith(marker) or marker in name for marker in _COMPLETION_TOKEN_MARKERS)


def build_chat_payload(
    config: AIModelConfig,
    user_prompt: str,
    max_tokens: int,
    *,
    use_completion_tokens: bool,
    include_temperature: bool,
    system_prompt: str = SYSTEM_PROMPT,
    history: list[dict] | None = None,
) -> dict:
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})
    payload: dict = {
        "model": config.model_name,
        "messages": messages,
    }
    if include_temperature:
        payload["temperature"] = config.temperature
    if use_completion_tokens:
        payload["max_completion_tokens"] = max_tokens
    else:
        payload["max_tokens"] = max_tokens
    return payload


class AIService:
    def __init__(self, credentials: CredentialService):
        self._credentials = credentials

    def test_connection(self, config: AIModelConfig, raw_key: str | None = None) -> str:
        key = raw_key if raw_key is not None else self._credentials.decrypt(config.encrypted_api_key)
        self._chat(config, key, "只回复：ok", max_tokens=32)
        return "模型连接成功"

    def generate_report(self, config: AIModelConfig, user_prompt: str) -> str:
        key = self._credentials.decrypt(config.encrypted_api_key)
        return self._chat(config, key, user_prompt, max_tokens=config.max_tokens)

    def optimize(self, config: AIModelConfig, content: str, instruction: str) -> str:
        key = self._credentials.decrypt(config.encrypted_api_key)
        prompt = (
            f"请按以下要求优化周报，不要新增未出现的工作事项。\n"
            f"要求：{instruction}\n\n原文：\n{content}"
        )
        return self._chat(config, key, prompt, max_tokens=config.max_tokens)

    def ask(self, config: AIModelConfig, history: list[dict]) -> str:
        key = self._credentials.decrypt(config.encrypted_api_key)
        return self._chat(
            config,
            key,
            "",
            max_tokens=config.max_tokens,
            system_prompt=QA_SYSTEM_PROMPT,
            history=history,
        )

    def _chat(
        self,
        config: AIModelConfig,
        api_key: str,
        user_prompt: str,
        max_tokens: int,
        system_prompt: str = SYSTEM_PROMPT,
        history: list[dict] | None = None,
    ) -> str:
        if not api_key.strip():
            raise AIClientError("请先填写 Token")
        base = (config.api_base or "").rstrip("/")
        if not base:
            raise AIClientError("请先填写 API Base")
        url = base + "/chat/completions"
        use_completion = prefers_completion_tokens(config.model_name)
        include_temperature = True
        last_detail = ""
        last_code = 0
        for _ in range(3):
            payload = build_chat_payload(
                config,
                user_prompt,
                max_tokens,
                use_completion_tokens=use_completion,
                include_temperature=include_temperature,
                system_prompt=system_prompt,
                history=history,
            )
            try:
                body = self._post(url, api_key, payload)
                return self._extract_text(body)
            except HTTPError as exc:
                last_code = exc.code
                last_detail = exc.read().decode("utf-8", errors="ignore")
                lowered = last_detail.lower()
                if exc.code == 400 and "max_completion_tokens" in lowered and not use_completion:
                    use_completion = True
                    continue
                if exc.code == 400 and "max_tokens" in lowered and "unsupported" in lowered and use_completion:
                    use_completion = False
                    continue
                if (
                    exc.code == 400
                    and include_temperature
                    and "temperature" in lowered
                    and ("unsupported" in lowered or "not support" in lowered)
                ):
                    include_temperature = False
                    continue
                raise AIClientError(self._format_http_error(exc.code, last_detail)) from exc
            except URLError as exc:
                raise AIClientError(f"连接超时或无法访问\n{exc.reason}") from exc
        raise AIClientError(self._format_http_error(last_code, last_detail))

    def _post(self, url: str, api_key: str, payload: dict) -> dict:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))

    def _extract_text(self, body: dict) -> str:
        try:
            message = body["choices"][0]["message"]
            content = message.get("content")
            if isinstance(content, list):
                text = "".join(part.get("text", "") for part in content if isinstance(part, dict))
            else:
                text = content or ""
            text = text.strip()
            if text:
                return text
            raise KeyError("empty content")
        except (KeyError, IndexError, TypeError) as exc:
            raise AIClientError("模型返回格式无法解析") from exc

    def _format_http_error(self, code: int, detail: str) -> str:
        return f"连接失败 {code}\n{detail[:300]}"
