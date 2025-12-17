from __future__ import annotations
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from ml.extractor.schema import ClassifiedRecord

HATE_SPEECH_CLASS_INDEX = 1
MODEL_NAME = "beomi/KcELECTRA-base"
THRESHOLD = 0.3


class Classifier:
    _instance: "Classifier | None" = None

    def __new__(cls, model_name: str = MODEL_NAME):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model_name = model_name
        return cls._instance

    def __init__(self, model_name: str = MODEL_NAME):
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
            return probs[0][HATE_SPEECH_CLASS_INDEX].item()

    def classify(self, record_id: str, text: str) -> ClassifiedRecord:
        score = self.score(text)
        label = "hate" if score >= THRESHOLD else "normal"
        return ClassifiedRecord(
            id=record_id,
            text=text,
            score=score,
            label=label,
            model=MODEL_NAME,
        )

