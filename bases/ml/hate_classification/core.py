import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from ml.classifier.core import Classifier
from ml.extractor.schema import CleanRecord, ClassifiedRecord
from ml.json.core import Json
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MODEL_NAME: str = "beomi/KcELECTRA-base"
    THRESHOLD: float = 0.3
    CLEAN_DIR: str = "out/datalake/clean/dcinside/v1"
    CLASSIFIED_DIR: str = "out/datalake/classified/hate_speech/model=kcelectra"


def classify_data(today: str, settings: Settings) -> int:
    print(f"Starting classification for date: {today}")
    classified_dir = Path(settings.CLASSIFIED_DIR)
    classified_dir.mkdir(parents=True, exist_ok=True)
    classifier = Classifier(settings.MODEL_NAME)
    clean_path = Path(settings.CLEAN_DIR) / f"dt={today}" / "part-0001.jsonl"
    classified_path = classified_dir / f"dt={today}" / "part-0001.jsonl"
    classified_store = Json(classified_path)
    count = 0
    if not clean_path.exists():
        print(f"Clean data file does not exist: {clean_path}")
        return 0
    with clean_path.open("r", encoding="utf-8") as f:
        for line in f:
            clean_record: CleanRecord = json.loads(line)
            score = classifier.score(clean_record["text"])
            if score < settings.THRESHOLD:
                continue
            classified_record = classifier.classify(clean_record["id"], clean_record["text"])
            classified_store.append(classified_record)
            count += 1
    print(f"Classified {count} records for date {today}")
    return count


def run() -> None:
    settings = Settings()
    
    # Use Korea Standard Time (KST, UTC+9) for date calculation
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)
    target_date = (now_kst - timedelta(days=1)).strftime("%Y-%m-%d")  # yesterday in KST
    
    print(f"Current time (KST): {now_kst.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target date: {target_date}")
    
    count = classify_data(target_date, settings)
    print(f"Classification completed: {count} records")


if __name__ == "__main__":
    run()

