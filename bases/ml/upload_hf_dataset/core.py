import asyncio
import json
from pathlib import Path
from ml import config
from ml.extractor.schema import LabeledRecord
from ml.hate_speech import InstructionData
from ml.hf.core import Client as HfClient
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLM_MODEL: str = "OxW/Qwen3-0.6B-GGUF"
    LABELED_DIR: str = "out/datalake/labeled/hate_speech/llm=qwen3"


def format_instruction(labeled: LabeledRecord) -> InstructionData:
    instruction = "다음 텍스트를 분석하여 혐오표현 유형을 분류하세요. 혐오표현이 없다면 '없음'으로 표시하세요."
    hate_types_str = ", ".join(labeled["hate_type"]) if labeled["hate_type"] else "없음"
    output = f"혐오표현 유형: {hate_types_str}"
    return InstructionData(
        instruction=instruction,
        input=labeled["text"],
        output=output,
    )


async def upload_data(today: str, global_settings: config.Settings, local_settings: Settings) -> None:
    labeled_path = Path(local_settings.LABELED_DIR) / f"dt={today}" / "part-0001.jsonl"
    if not labeled_path.exists():
        return
    all_data = []
    with labeled_path.open("r", encoding="utf-8") as f:
        for line in f:
            labeled_record: LabeledRecord = json.loads(line)
            instruction = format_instruction(labeled_record)
            all_data.append(instruction)
    if not all_data:
        return
    async with HfClient(global_settings.hf_token, local_settings.LLM_MODEL, global_settings.hf_dataset_repo_id) as hf:
        await hf.upload(all_data)


async def main() -> None:
    global_settings = config.get_settings()
    local_settings = Settings()
    from datetime import datetime, timedelta

    target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")  # yesterday
    await upload_data(target_date, global_settings, local_settings)


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()

