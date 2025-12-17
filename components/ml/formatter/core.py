from __future__ import annotations

from ml.hate_speech import InstructionData, LabelResult, RawPost


class Formatter:
    HATE_SPEECH_INSTRUCTION = "다음 텍스트를 분석하여 혐오표현 유형을 분류하세요. 혐오표현이 없다면 '없음'으로 표시하세요."
    NUANCE_INSTRUCTION = "다음 텍스트의 뉘앙스를 분석하고, 혐오적이거나 부적절한 표현이 있는지 판단하세요."

    def transform(self, post: RawPost, label: LabelResult) -> InstructionData:
        if label.nuance:
            return InstructionData(
                instruction=self.NUANCE_INSTRUCTION,
                input=post.content,
                output=f"뉘앙스: {label.nuance}\n혐오 수준: {label.hate_level or 'N/A'}\n이유: {label.reason or 'N/A'}",
            )

        return InstructionData(
            instruction=self.HATE_SPEECH_INSTRUCTION,
            input=post.content,
            output=f"혐오표현 유형: {label.hate_speech_type}\n설명: {label.hate_speech_description}",
        )

