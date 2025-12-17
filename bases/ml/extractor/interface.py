from __future__ import annotations
from abc import ABC, abstractmethod
from ml.extractor.schema import CleanRecord


class BaseExtractor(ABC):
    source: str

    @abstractmethod
    def extract(self, raw: dict) -> CleanRecord:
        pass

    @abstractmethod
    def validate(self, record: CleanRecord) -> None:
        pass

