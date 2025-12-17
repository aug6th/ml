from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from ml.hate_speech import RawPost


class Scraper(Protocol):
    async def collect(self) -> AsyncIterator[RawPost]:
        ...

    async def get_progress(self) -> dict:
        ...

    async def save_progress(self, progress: dict) -> None:
        ...
