from __future__ import annotations

import httpx

from ml.llm.interfaces import LLMClient, LLMMessage, LLMRole


class OllamaClient(LLMClient):
    def __init__(self, base_url: str = "http://localhost:11434/v1", model: str = "qwen3-0.6b"):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "OllamaClient":
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=60.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.aclose()

    def get_model(self) -> str:
        return self._model

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        assert self._client is not None, "OllamaClient is not initialized"

        model_name = model or self._model
        payload: dict = {
            "model": model_name,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        resp = await self._client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        # OpenAI 호환 구조: choices[0].message.content
        return data["choices"][0]["message"]["content"]


