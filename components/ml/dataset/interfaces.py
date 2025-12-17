from __future__ import annotations

from typing import Protocol

from ml.hate_speech import InstructionData


class DatasetUploader(Protocol):
    async def upload(self, data: list[InstructionData]) -> str:
        ...
