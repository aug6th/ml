import re


def parse_label_response(response: str) -> dict | None:
    type_match = re.search(r"혐오표현 유형:\s*([^\n]+)", response)
    if not type_match:
        return None

    desc_match = re.search(r"설명:\s*([^\n]+(?:\n[^\n]+)*)", response)
    nuance_match = re.search(r"뉘앙스:\s*([^\n]+)", response)
    level_match = re.search(r"혐오 수준:\s*([^\n]+)", response)
    reason_match = re.search(r"이유:\s*([^\n]+(?:\n[^\n]+)*)", response)

    result = {
        "type": type_match.group(1).strip(),
        "description": desc_match.group(1).strip() if desc_match else "",
    }
    if nuance_match or level_match:
        result.update({
            "nuance": nuance_match.group(1).strip() if nuance_match else None,
            "hate_level": level_match.group(1).strip() if level_match else None,
            "reason": reason_match.group(1).strip() if reason_match else None,
        })
    return result

