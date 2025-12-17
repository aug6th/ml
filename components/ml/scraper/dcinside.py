from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator
from datetime import date
from pathlib import Path
from ml.hate_speech import RawPost
from ml.http.core import Client as HttpClient
from ml.json.core import Json
from ml.scraper.parser import parse_gallery_page, parse_post_detail

class DcinsideScraper:
    def __init__(self, http: HttpClient, galleries: list[str], max_posts: int, checkpoint_path: Path, rate_limit: float = 1.0):
        self._http = http
        self._galleries = galleries
        self._max_posts = max_posts
        self._checkpoint = Json(checkpoint_path)
        self._rate_limit = rate_limit
        self._today = date.today()

    async def collect(self) -> AsyncIterator[RawPost]:
        progress = self._checkpoint.get_all()
        for gallery in self._galleries:
            gp = progress.get(gallery, {"count": 0})
            if self._max_posts > 0 and gp["count"] >= self._max_posts:
                continue
            async for post in self._collect_gallery(gallery, gp):
                yield post
                gp["count"] = gp.get("count", 0) + 1
                progress[gallery] = gp
                self._checkpoint.set_all(progress)
                await asyncio.sleep(1.0 / self._rate_limit)

    async def _collect_gallery(self, gallery: str, progress: dict) -> AsyncIterator[RawPost]:
        page, collected = 1, progress.get("count", 0)
        while self._max_posts <= 0 or collected < self._max_posts:
            resp = await self._http.get("/board/lists", {"id": gallery, "page": page})
            posts = parse_gallery_page(resp.text)
            if not posts:
                break
            for post_id, title in posts:
                resp = await self._http.get("/board/view", {"id": gallery, "no": post_id})
                post = parse_post_detail(resp.text, gallery, post_id, title)
                if not post or not post.content:
                    continue
                if post.created_at and post.created_at.date() != self._today:
                    return
                yield post
                collected += 1
                if self._max_posts > 0 and collected >= self._max_posts:
                    return
            page += 1
            await asyncio.sleep(1.0 / self._rate_limit)
