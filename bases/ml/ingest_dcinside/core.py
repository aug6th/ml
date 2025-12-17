import asyncio
import json
from datetime import date, datetime
from pathlib import Path
from ml import config
from ml.dcinside_extractor.extractor import DCInsideExtractor
from ml.http.core import Client as HttpClient
from ml.json.core import Json
from ml.scraper.parser import parse_gallery_page, parse_post_detail
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BATCH_SIZE: int = 100
    RATE_LIMIT: float = 1.0
    RAW_DIR: str = "out/datalake/raw/dcinside"
    CLEAN_DIR: str = "out/datalake/clean/dcinside/v1"
    CHECKPOINT_PATH: str = "out/datalake/checkpoints/ingest_dcinside.json"
    DCINSIDE_BASE_URL: str = "https://gall.dcinside.com"


async def collect_raw(galleries: list[str], today: str, settings: Settings) -> int:
    raw_dir = Path(settings.RAW_DIR)
    raw_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = Path(settings.CHECKPOINT_PATH)
    checkpoint = Json(checkpoint_path)
    progress = checkpoint.get_all()
    count = 0
    async with HttpClient(settings.DCINSIDE_BASE_URL) as http:
        for gallery in galleries:
            gp = progress.get(gallery, {"count": 0, "last_page": 1})
            page = gp.get("last_page", 1)
            collected = gp.get("count", 0)
            raw_path = raw_dir / f"dt={today}" / f"{gallery}.jsonl"
            raw_store = Json(raw_path)
            while collected < settings.BATCH_SIZE:
                resp = await http.get("/board/lists", {"id": gallery, "page": page})
                posts = parse_gallery_page(resp.text)
                if not posts:
                    break
                for post_id, title in posts:
                    resp = await http.get("/board/view", {"id": gallery, "no": post_id})
                    post = parse_post_detail(resp.text, gallery, post_id, title)
                    if not post or not post.content:
                        continue
                    if post.created_at and post.created_at.date() != date.today():
                        return count
                    raw_store.append(post.to_dict())
                    count += 1
                    collected += 1
                    if collected >= settings.BATCH_SIZE:
                        break
                page += 1
                gp["count"] = collected
                gp["last_page"] = page
                progress[gallery] = gp
                checkpoint.set_all(progress)
                await asyncio.sleep(1.0 / settings.RATE_LIMIT)
                if collected >= settings.BATCH_SIZE:
                    break
    return count


async def clean_data(today: str, settings: Settings) -> int:
    clean_dir = Path(settings.CLEAN_DIR)
    clean_dir.mkdir(parents=True, exist_ok=True)
    extractor = DCInsideExtractor()
    clean_path = clean_dir / f"dt={today}" / "part-0001.jsonl"
    clean_store = Json(clean_path)
    count = 0
    raw_dir = Path(settings.RAW_DIR) / f"dt={today}"
    if not raw_dir.exists():
        return 0
    for raw_file in raw_dir.glob("*.jsonl"):
        with raw_file.open("r", encoding="utf-8") as f:
            for line in f:
                raw = json.loads(line)
                try:
                    clean_record = extractor.extract(raw)
                    extractor.validate(clean_record)
                    clean_store.append(clean_record)
                    count += 1
                except (ValueError, KeyError):
                    continue
    return count


async def main() -> None:
    global_settings = config.get_settings()
    local_settings = Settings()
    today = datetime.now().strftime("%Y-%m-%d")
    await collect_raw(global_settings.crawl_galleries, today, local_settings)
    await clean_data(today, local_settings)


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()

