from __future__ import annotations
import re
from cleantext import clean


def clean_text(text: str) -> str:
    url_pattern = r'https?://[^\s]+|www\.[^\s]+'
    text = re.sub(url_pattern, '', text)
    
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    text = re.sub(email_pattern, '', text)
    
    phone_pattern = r'\d{2,3}-\d{3,4}-\d{4}|\d{10,11}'
    text = re.sub(phone_pattern, '', text)
    
    cleaned = clean(
        text,
        clean_all=False,
        extra_spaces=True,
        stemming=False,
        stopwords=False,
        lowercase=False,
        numbers=False,
        punct=False,
        stp_lang='english',
    )
    return cleaned.strip()

