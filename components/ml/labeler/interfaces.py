from __future__ import annotations

from typing import Protocol

from ml.hate_speech import LabelResult, RawPost


class Labeler(Protocol):
    async def label(self, post: RawPost) -> LabelResult | None:
        ...
