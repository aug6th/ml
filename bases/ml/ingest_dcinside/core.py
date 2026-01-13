import asyncio
import json
from datetime import date, datetime, timedelta, timezone
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
    print(f"Starting raw data collection for date: {today}, galleries: {galleries}")
    raw_dir = Path(settings.RAW_DIR)
    raw_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = Path(settings.CHECKPOINT_PATH)
    checkpoint = Json(checkpoint_path)
    progress = checkpoint.get_all()
    count = 0
    async with HttpClient(settings.DCINSIDE_BASE_URL) as http:
        for gallery in galleries:
            # Use date-specific checkpoint key to avoid conflicts between dates
            gallery_key = f"{gallery}_{today}"
            gp = progress.get(gallery_key, {"count": 0, "last_page": 1})
            page = gp.get("last_page", 1)
            collected = gp.get("count", 0)
            print(f"Gallery {gallery}: starting from page {page}, already collected {collected} posts")
            raw_path = raw_dir / f"dt={today}" / f"{gallery}.jsonl"
            raw_store = Json(raw_path)
            consecutive_old_posts = 0
            pages_processed = 0
            while collected < settings.BATCH_SIZE:
                resp = await http.get("/board/lists", {"id": gallery, "page": page})
                posts = parse_gallery_page(resp.text)
                if not posts:
                    print(f"Gallery {gallery}: No posts found on page {page}, stopping")
                    break
                pages_processed += 1
                posts_on_target_date = 0
                for post_id, title in posts:
                    resp = await http.get("/board/view", {"id": gallery, "no": post_id})
                    post = parse_post_detail(resp.text, gallery, post_id, title)
                    if not post or not post.content:
                        continue
                    if not post.dt:
                        continue
                    if post.dt < today:
                        consecutive_old_posts += 1
                        if consecutive_old_posts >= 10:
                            print(f"Gallery {gallery}: Found 10 consecutive old posts, stopping collection")
                            break
                        continue
                    if post.dt > today:
                        continue
                    if post.dt == today:
                        consecutive_old_posts = 0
                        raw_store.append(post.model_dump())
                        count += 1
                        collected += 1
                        posts_on_target_date += 1
                        if collected >= settings.BATCH_SIZE:
                            break
                if consecutive_old_posts >= 10:
                    break
                if pages_processed % 5 == 0:
                    print(f"Gallery {gallery}: Processed {pages_processed} pages, collected {collected} posts for date {today}")
                page += 1
                gp["count"] = collected
                gp["last_page"] = page
                progress[gallery_key] = gp
                checkpoint.set_all(progress)
                await asyncio.sleep(1.0 / settings.RATE_LIMIT)
                if collected >= settings.BATCH_SIZE:
                    break
            print(f"Gallery {gallery}: Finished with {collected} posts collected for date {today}")
    print(f"Collected {count} raw posts for date {today}")
    return count


async def clean_data(today: str, settings: Settings) -> int:
    print(f"Starting data cleaning for date: {today}")
    clean_dir = Path(settings.CLEAN_DIR)
    clean_dir.mkdir(parents=True, exist_ok=True)
    extractor = DCInsideExtractor()
    clean_path = clean_dir / f"dt={today}" / "part-0001.jsonl"
    clean_store = Json(clean_path)
    count = 0
    raw_dir = Path(settings.RAW_DIR) / f"dt={today}"
    if not raw_dir.exists():
        print(f"Raw directory does not exist: {raw_dir}")
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
    print(f"Cleaned {count} records for date {today}")
    return count


async def main() -> None:
    global_settings = config.get_settings()
    local_settings = Settings()
    
    # Use Korea Standard Time (KST, UTC+9) for date calculation
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)
    target_date = (now_kst - timedelta(days=1)).strftime("%Y-%m-%d")  # yesterday in KST
    
    print(f"Current time (KST): {now_kst.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target date: {target_date}")
    
    raw_count = await collect_raw(global_settings.crawl_galleries, target_date, local_settings)
    clean_count = await clean_data(target_date, local_settings)
    
    print(f"Pipeline completed: raw={raw_count}, clean={clean_count}")


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()

