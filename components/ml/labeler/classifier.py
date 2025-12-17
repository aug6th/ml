from __future__ import annotations

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class Classifier:
    HATE_SPEECH_CLASS_INDEX = 1
    _instance: "Classifier | None" = None

    def __new__(cls, model_name: str = "beomi/KcELECTRA-base"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model_name = model_name
        return cls._instance

    def __init__(self, model_name: str = "beomi/KcELECTRA-base"):
        if hasattr(self, "_initialized"):
            return
        self.tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self._model_name)
        self.model.eval()
        self._initialized = True

    def score(self, text: str) -> float:
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)
            return probs[0][self.HATE_SPEECH_CLASS_INDEX].item()
