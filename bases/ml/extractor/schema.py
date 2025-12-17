from __future__ import annotations
from typing import TypedDict


class CleanRecord(TypedDict):
    id: str
    source: str
    text: str
    created_at: str | None
    meta: dict


class ClassifiedRecord(TypedDict):
    id: str
    text: str
    score: float
    label: str
    model: str


class LabeledRecord(TypedDict):
    id: str
    text: str
    hate: bool
    hate_type: list[str]
    llm_model: str
    confidence: float

