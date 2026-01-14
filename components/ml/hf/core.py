from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from datasets import Dataset, DatasetDict, load_dataset
from huggingface_hub import HfApi
from ml.hate_speech import InstructionData
from ml.http.core import Client as HttpClient
from ml.llm import LLMMessage
from ml.llm.interfaces import LLMClient

class Client(LLMClient):
    BASE_URL = "https://api-inference.huggingface.co"

    def __init__(self, token: str, model: str, repo_id: str):
        self._token = token
        self._model = model
        self._repo_id = repo_id
        self._http: HttpClient | None = None

    async def __aenter__(self):
        self._http = HttpClient(self.BASE_URL)
        await self._http.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._http:
            await self._http.__aexit__(exc_type, exc_val, exc_tb)

    def get_model(self) -> str:
        return self._model

    async def generate(self, messages: list[LLMMessage], *, model: str | None = None, temperature: float | None = None, max_tokens: int | None = None) -> str:
        model_name = model or self._model
        prompt = messages[-1].content if messages else ""
        payload = {"inputs": prompt, "parameters": {}}
        if temperature is not None:
            payload["parameters"]["temperature"] = temperature
        if max_tokens is not None:
            payload["parameters"]["max_new_tokens"] = max_tokens
        headers = {"Authorization": f"Bearer {self._token}"}
        resp = await self._http.post(f"/models/{model_name}", json=payload, headers=headers)
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"HuggingFace API error: {data['error']}")
        if isinstance(data, list) and len(data) > 0:
            return data[0].get("generated_text", "")
        return data.get("generated_text", "")

    async def upload(self, data: list[InstructionData] | list[dict]) -> str:
        # 새 데이터를 dict 리스트로 변환
        new_data = [item.model_dump() if isinstance(item, InstructionData) else item for item in data]
        
        version_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._upload_sync, new_data, version_tag)
        return f"https://huggingface.co/datasets/{self._repo_id}"

    def _upload_sync(self, new_data: list[dict], version_tag: str) -> None:
        api = HfApi(token=self._token)
        api.create_repo(repo_id=self._repo_id, repo_type="dataset", exist_ok=True)
        
        # 기존 데이터셋 로드 시도 (존재하지 않으면 None)
        try:
            existing_dataset = load_dataset(self._repo_id, token=self._token)
            print(f"Loaded existing dataset with {len(existing_dataset['train'])} train, {len(existing_dataset.get('validation', []))} validation, {len(existing_dataset.get('test', []))} test samples")
            
            # 기존 데이터를 리스트로 변환
            existing_train = existing_dataset["train"].to_list()
            existing_val = existing_dataset.get("validation", Dataset.from_list([])).to_list()
            existing_test = existing_dataset.get("test", Dataset.from_list([])).to_list()
            
            # 새 데이터를 기존 데이터에 추가
            all_data = existing_train + existing_val + existing_test + new_data
            print(f"Total data after merge: {len(all_data)} samples (existing: {len(existing_train) + len(existing_val) + len(existing_test)}, new: {len(new_data)})")
        except Exception as e:
            # 데이터셋이 존재하지 않거나 로드 실패 시 새 데이터만 사용
            print(f"Could not load existing dataset (may not exist yet): {e}")
            all_data = new_data
            print(f"Using only new data: {len(all_data)} samples")
        
        # 전체 데이터를 train/val/test로 분할
        train_size = int(len(all_data) * 0.8)
        val_size = int(len(all_data) * 0.1)
        train_data = all_data[:train_size]
        val_data = all_data[train_size:train_size + val_size]
        test_data = all_data[train_size + val_size:]
        
        dataset_dict = DatasetDict({
            "train": Dataset.from_list(train_data),
            "validation": Dataset.from_list(val_data),
            "test": Dataset.from_list(test_data),
        })
        
        print(f"Uploading dataset: train={len(train_data)}, validation={len(val_data)}, test={len(test_data)}")
        dataset_dict.push_to_hub(repo_id=self._repo_id, token=self._token, commit_message=f"Update dataset - {version_tag}")
