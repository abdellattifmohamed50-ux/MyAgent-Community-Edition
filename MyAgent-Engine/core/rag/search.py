from __future__ import annotations

import re
from collections import Counter

from core.rag.chunking import chunk_text

_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")
_TOKEN = re.compile(r"[\w]+", re.UNICODE)
_ARABIC_EQUIVALENTS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"})


class BM25Lite:
    """Dependency-free Unicode lexical ranker for small private knowledge sets."""

    def terms(self, text: str) -> list[str]:
        normalized = _DIACRITICS.sub("", text.lower().translate(_ARABIC_EQUIVALENTS))
        return [term for term in _TOKEN.findall(normalized) if len(term) > 1]

    def candidate_terms(self, text: str) -> list[str]:
        raw = _DIACRITICS.sub("", text.lower())
        original = [term for term in _TOKEN.findall(raw) if len(term) > 1]
        return list(dict.fromkeys([*original, *self.terms(text)]))

    def score(self, query: str, document: str, title: str = "") -> float:
        query_terms = self.terms(query)
        if not query_terms:
            return 0.0
        document_terms = self.terms(document)
        if not document_terms:
            return 0.0
        title_counts = Counter(self.terms(title))
        document_counts = Counter(document_terms)
        unique_query = set(query_terms)
        matched = sum(1 for term in unique_query if document_counts[term] or title_counts[term])
        frequency = sum(min(document_counts[term], 4) for term in unique_query)
        title_bonus = sum(min(title_counts[term], 2) * 2.0 for term in unique_query)
        coverage = matched / len(unique_query)
        length_normalizer = 1.0 + max(0, len(document_terms) - 400) / 2_000
        return (frequency + title_bonus + coverage * 4.0) / length_normalizer

    def best_excerpt(self, query: str, document: str, max_chars: int) -> str:
        if len(document) <= max_chars:
            return document.strip()
        overlap = min(180, max_chars // 4)
        chunks = chunk_text(document, chunk_size=max_chars, overlap=overlap)
        return max(chunks, key=lambda item: self.score(query, item)).strip()
