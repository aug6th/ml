from __future__ import annotations
import re
from ml.extractor.schema import LabeledRecord
from ml.llm.interfaces import LLMClient, LLMMessage, LLMRole


def parse_label_response(response: str) -> dict | None:
    type_match = re.search(r"혐오표현 유형:\s*([^\n]+)", response)
    if not type_match:
        return None
    desc_match = re.search(r"설명:\s*([^\n]+(?:\n[^\n]+)*)", response)
    result = {
        "type": type_match.group(1).strip(),
        "description": desc_match.group(1).strip() if desc_match else "",
    }
    return result

HATE_PROMPT = """다음 텍스트를 분석하여 혐오표현 유형을 분류하세요.
분류 가능한 유형: 성별혐오, 인종혐오, 종교혐오, 장애혐오, 기타혐오, 없음
응답 형식:
혐오표현 유형: [유형]
설명: [설명]
텍스트: {text}"""

TEMPERATURE = 0.3


class LLMLabeler:
    def __init__(self, llm: LLMClient, model_name: str):
        self._llm = llm
        self._model_name = model_name

    async def label(self, record_id: str, text: str) -> LabeledRecord:
        prompt = HATE_PROMPT.format(text=text)
        messages = [LLMMessage(role=LLMRole.USER, content=prompt)]
        response = await self._llm.generate(messages, model=self._model_name, temperature=TEMPERATURE)
        parsed = parse_label_response(response)
        if not parsed:
            return LabeledRecord(
                id=record_id,
                text=text,
                hate=False,
                hate_type=[],
                llm_model=self._model_name,
                confidence=0.0,
            )
        hate_type_str = parsed.get("type", "없음")
        hate = hate_type_str != "없음"
        hate_types = [hate_type_str] if hate else []
        return LabeledRecord(
            id=record_id,
            text=text,
            hate=hate,
            hate_type=hate_types,
            llm_model=self._model_name,
            confidence=1.0,
        )

