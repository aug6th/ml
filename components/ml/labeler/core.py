from ml.hate_speech import LabelResult, RawPost
from ml.labeler.classifier import Classifier
from ml.labeler.parser import parse_label_response
from ml.llm import LLMMessage, LLMRole
from ml.llm.interfaces import LLMClient

HATE_PROMPT = """다음 텍스트를 분석하여 혐오표현 유형을 분류하세요.
분류 가능한 유형: 성별혐오, 인종혐오, 종교혐오, 장애혐오, 기타혐오, 없음
응답 형식:
혐오표현 유형: [유형]
설명: [설명]
텍스트: {text}"""

class Labeler:
    def __init__(self, llm: LLMClient, classifier: Classifier | None, threshold: float = 0.3):
        self._llm = llm
        self._classifier = classifier
        self._threshold = threshold

    async def label(self, post: RawPost) -> LabelResult | None:
        if self._classifier:
            score = self._classifier.score(post.content)
            if score < self._threshold:
                return None
        result = await self._call_llm(HATE_PROMPT.format(text=post.content))
        if not result:
            return None
        return LabelResult(
            hate_speech_type=result.get("type", "없음"),
            hate_speech_description=result.get("description", ""),
            nuance=result.get("nuance"),
            hate_level=result.get("hate_level"),
            reason=result.get("reason"),
        )

    async def _call_llm(self, prompt: str) -> dict | None:
        messages = [LLMMessage(role=LLMRole.USER, content=prompt)]
        response = await self._llm.generate(messages, model=self._llm.get_model(), temperature=0.3)
        return parse_label_response(response)
