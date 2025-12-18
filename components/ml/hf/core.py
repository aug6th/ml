from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from datasets import Dataset, DatasetDict
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
        train_size = int(len(data) * 0.8)
        val_size = int(len(data) * 0.1)
        train_data = [item.model_dump() for item in data[:train_size]]
        val_data = [item.model_dump() for item in data[train_size:train_size + val_size]]
        test_data = [item.model_dump() for item in data[train_size + val_size:]]
        dataset_dict = DatasetDict({
            "train": Dataset.from_list(train_data),
            "validation": Dataset.from_list(val_data),
            "test": Dataset.from_list(test_data),
        })
        version_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._upload_sync, dataset_dict, version_tag)
        return f"https://huggingface.co/datasets/{self._repo_id}"

    def _upload_sync(self, dataset_dict: DatasetDict, version_tag: str) -> None:
        api = HfApi(token=self._token)
        api.create_repo(repo_id=self._repo_id, repo_type="dataset", exist_ok=True)
        dataset_dict.push_to_hub(repo_id=self._repo_id, token=self._token, commit_message=f"Update dataset - {version_tag}")
