import asyncio
import json
from pathlib import Path

from ml import config
from ml.extractor.schema import ClassifiedRecord, LabeledRecord
from ml.json.core import Json
from ml.llm.ollama_client import OllamaClient
from ml.llm_labeler.core import LLMLabeler
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLM_MODEL: str = "OxW/Qwen3-0.6B-GGUF"
    CLASSIFIED_DIR: str = "out/datalake/classified/hate_speech/model=kcelectra"
    LABELED_DIR: str = "out/datalake/labeled/hate_speech/llm=qwen3"
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"


async def label_data(today: str, global_settings: config.Settings, local_settings: Settings) -> int:
    labeled_dir = Path(local_settings.LABELED_DIR)
    labeled_dir.mkdir(parents=True, exist_ok=True)
    classified_path = Path(local_settings.CLASSIFIED_DIR) / f"dt={today}" / "part-0001.jsonl"
    labeled_path = labeled_dir / f"dt={today}" / "part-0001.jsonl"
    labeled_store = Json(labeled_path)
    count = 0
    if not classified_path.exists():
        return 0

    async with OllamaClient(
        base_url=local_settings.OLLAMA_BASE_URL,
        model=local_settings.LLM_MODEL,
    ) as llm:
        labeler = LLMLabeler(llm, local_settings.LLM_MODEL)
        with classified_path.open("r", encoding="utf-8") as f:
            for line in f:
                classified_record: ClassifiedRecord = json.loads(line)
                labeled_record = await labeler.label(classified_record["id"], classified_record["text"])
                labeled_store.append(labeled_record)
                count += 1
    return count


async def main() -> None:
    global_settings = config.get_settings()
    local_settings = Settings()
    from datetime import datetime, timedelta

    target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")  # yesterday
    await label_data(target_date, global_settings, local_settings)


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()

