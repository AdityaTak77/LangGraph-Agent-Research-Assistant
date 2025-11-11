# ==========================================
# utils/text_utils.py
# ==========================================
"""
Utility functions for text preprocessing, cleaning, and chunking.
Used by the SearchAgent and SummarizerAgent.
"""
import re
from typing import List


def clean_text(text: str) -> str:
    """
    Basic cleanup: remove extra spaces, control chars, etc.
    """
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = text.replace("\u00a0", " ").strip()
    return text


def chunk_text(text: str, max_words: int = 200) -> List[str]:
    """
    Split text into roughly equal word chunks (for large inputs).
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i:i + max_words])
        chunks.append(chunk)
    return chunks


def truncate_text(text: str, max_chars: int = 1000) -> str:
    """
    Truncate long text safely.
    """
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """
    Very simple keyword extractor (by frequency).
    """
    words = re.findall(r"[A-Za-z]{4,}", text.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:top_n]]
