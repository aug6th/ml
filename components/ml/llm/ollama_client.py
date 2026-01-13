from __future__ import annotations

import asyncio

import httpx

from ml.llm.interfaces import LLMClient, LLMMessage, LLMRole


class OllamaClient(LLMClient):
    def __init__(self, base_url: str = "http://localhost:11434/v1", model: str = "qwen3-0.6b"):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "OllamaClient":
        # Ollama 호출이 길어질 수 있으므로 여유 있는 타임아웃 사용
        timeout = httpx.Timeout(300.0, connect=30.0)
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)
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

        # GitHub Actions에서 httpx.ReadTimeout이 자주 발생해 재시도 로직 추가
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                resp = await self._client.post("/chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()
                # OpenAI 호환 구조: choices[0].message.content
                return data["choices"][0]["message"]["content"]
            except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                last_error = e
                # 마지막 시도가 아니면 지수 백오프로 재시도
                if attempt < 2:
                    backoff = 2 ** attempt
                    await asyncio.sleep(backoff)
                    continue
                raise
        # 논리상 여기까지 오지 않지만 mypy/타입을 위해
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected error in OllamaClient.generate")


