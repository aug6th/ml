import asyncio
import json
from datetime import date, datetime
from pathlib import Path
from ml import config
from ml.hate_speech import InstructionData, RawPost
from ml.formatter.core import Formatter
from ml.hf.core import Client as HfClient
from ml.http.core import Client as HttpClient
from ml.json.core import Json
from ml.labeler.classifier import Classifier
from ml.labeler.core import Labeler
from ml.scraper.dcinside import DcinsideScraper

RAW_DIR = Path("out/data/raw")
LABELED_DIR = Path("out/data/labeled")
CHECKPOINT_PATH = Path("out/data/checkpoints/progress.json")
COLLECT_BATCH_SIZE = 100

async def collect_raw_posts(today: str, settings: config.Settings) -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    galleries = settings.crawl_galleries
    classifier = Classifier(settings.classifier_model) if settings.enable_classifier else None
    print(f"Collecting: galleries={galleries}, date={date.today()}, batch_size={COLLECT_BATCH_SIZE}")
    count = 0
    async with HttpClient("https://gall.dcinside.com") as http:
        scraper = DcinsideScraper(http, galleries, COLLECT_BATCH_SIZE, CHECKPOINT_PATH, settings.crawl_rate_limit)
        async for post in scraper.collect():
            if classifier:
                score = classifier.score(post.content)
                if score < settings.classifier_threshold:
                    continue
            raw_path = RAW_DIR / f"{today}_{post.gallery}.jsonl"
            Json(raw_path).append(post.to_dict())
            count += 1
            print(f"[{count}] {post.gallery}/{post.post_id}: {post.title[:30]}")
    print(f"Collected: {count} posts")
    return count

async def label_and_upload(today: str, settings: config.Settings) -> int:
    LABELED_DIR.mkdir(parents=True, exist_ok=True)
    formatter = Formatter()
    labeled_count = 0
    async with HfClient(settings.hf_token, settings.hf_inference_model, settings.hf_dataset_repo_id) as hf:
        labeler = Labeler(hf, None, settings.classifier_threshold)
        for gallery in settings.crawl_galleries:
            raw_path = RAW_DIR / f"{today}_{gallery}.jsonl"
            if not raw_path.exists():
                continue
            labeled_path = LABELED_DIR / f"{today}_{gallery}.jsonl"
            labeled_store = Json(labeled_path)
            with raw_path.open("r", encoding="utf-8") as f:
                for line in f:
                    post = RawPost.from_dict(json.loads(line))
                    label = await labeler.label(post)
                    if not label:
                        continue
                    instruction = formatter.transform(post, label)
                    labeled_store.append(instruction.to_dict())
                    labeled_count += 1
                    print(f"Labeled: {post.post_id} -> {label.hate_speech_type}")
        all_data = []
        for gallery in settings.crawl_galleries:
            labeled_path = LABELED_DIR / f"{today}_{gallery}.jsonl"
            if not labeled_path.exists():
                continue
            with labeled_path.open("r", encoding="utf-8") as f:
                all_data.extend([InstructionData(**json.loads(line)) for line in f])
        if all_data:
            print(f"Uploading: {len(all_data)} items")
            await hf.upload(all_data)
            print("Upload completed")
    return labeled_count

async def run_pipeline() -> None:
    settings = config.get_settings()
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"Pipeline started: {today}")
    await collect_raw_posts(today, settings)
    await label_and_upload(today, settings)
    print("Pipeline finished")

def main() -> None:
    asyncio.run(run_pipeline())
