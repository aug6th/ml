from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional

class DtMixin(BaseModel):
    dt: Optional[str] = None

class RawComment(DtMixin):
    comment_id: str
    content: str
    author: Optional[str] = None

class RawPost(DtMixin):
    post_id: str
    gallery: str
    title: str
    content: str
    author: Optional[str] = None
    comments: list[RawComment] = Field(default_factory=list)
    url: Optional[str] = None

class LabelResult(BaseModel):
    hate_speech_type: str
    hate_speech_description: str
    nuance: Optional[str] = None
    hate_level: Optional[str] = None
    reason: Optional[str] = None

class InstructionData(BaseModel):
    instruction: str
    input: str
    output: str
