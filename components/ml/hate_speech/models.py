from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RawComment:
    comment_id: str
    content: str
    author: str | None
    created_at: datetime | None

    def to_dict(self) -> dict:
        return {
            "comment_id": self.comment_id,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

@dataclass
class RawPost:
    post_id: str
    gallery: str
    title: str
    content: str
    author: str | None
    created_at: datetime | None
    comments: list[RawComment]
    url: str | None = None

    def to_dict(self) -> dict:
        return {
            "post_id": self.post_id,
            "gallery": self.gallery,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "comments": [c.to_dict() for c in self.comments],
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RawPost:
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        return cls(
            post_id=data["post_id"],
            gallery=data["gallery"],
            title=data["title"],
            content=data["content"],
            author=data.get("author"),
            created_at=created_at,
            comments=[],
            url=data.get("url"),
        )

@dataclass
class LabelResult:
    hate_speech_type: str
    hate_speech_description: str
    nuance: str | None = None
    hate_level: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict:
        return {
            "hate_speech_type": self.hate_speech_type,
            "hate_speech_description": self.hate_speech_description,
            "nuance": self.nuance,
            "hate_level": self.hate_level,
            "reason": self.reason,
        }

@dataclass
class InstructionData:
    instruction: str
    input: str
    output: str

    def to_dict(self) -> dict:
        return {
            "instruction": self.instruction,
            "input": self.input,
            "output": self.output,
        }
