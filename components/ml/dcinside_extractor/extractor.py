from __future__ import annotations
from datetime import datetime
from ml.extractor.interface import BaseExtractor
from ml.extractor.schema import CleanRecord
from ml.dcinside_extractor.cleaner import clean_text


class DCInsideExtractor(BaseExtractor):
    source = "dcinside"

    def extract(self, raw: dict) -> CleanRecord:
        post_id = raw.get("post_id", "")
        gallery = raw.get("gallery", "")
        title = raw.get("title", "")
        content = raw.get("content", "")
        created_at = raw.get("created_at")
        url = raw.get("url", "")

        text = f"{title}\n{content}".strip()
        cleaned_text = clean_text(text)

        created_at_str = None
        if created_at:
            if isinstance(created_at, str):
                created_at_str = created_at
            elif isinstance(created_at, datetime):
                created_at_str = created_at.isoformat()

        return CleanRecord(
            id=f"{gallery}_{post_id}",
            source=self.source,
            text=cleaned_text,
            created_at=created_at_str,
            meta={
                "gallery": gallery,
                "post_id": post_id,
                "url": url,
                "title": title,
            },
        )

    def validate(self, record: CleanRecord) -> None:
        if not record["id"]:
            raise ValueError("id is required")
        if not record["text"]:
            raise ValueError("text is required")
        if len(record["text"]) < 10:
            raise ValueError("text too short")
        if len(record["text"]) > 5000:
            raise ValueError("text too long")

