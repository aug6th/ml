from __future__ import annotations
import httpx
from ml.utils.retry import retry

class Client:
    def __init__(self, base_url: str, user_agent: str = ""):
        self._base_url = base_url.rstrip("/")
        self._user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=30.0,
            headers={"User-Agent": self._user_agent},
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    @retry(max_attempts=3, delay=5.0, exceptions=(httpx.HTTPError,))
    async def get(self, path: str, params: dict | None = None) -> httpx.Response:
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp

    @retry(max_attempts=3, delay=5.0, exceptions=(httpx.HTTPError,))
    async def post(self, path: str, json: dict | None = None, headers: dict | None = None) -> httpx.Response:
        resp = await self._client.post(path, json=json, headers=headers)
        resp.raise_for_status()
        return resp
