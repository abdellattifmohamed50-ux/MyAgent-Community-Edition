from __future__ import annotations

from core.rag.chunking import chunk_text


def test_chunk_text_creates_overlapping_chunks() -> None:
    chunks = chunk_text("abcdefghij", chunk_size=5, overlap=2)
    assert chunks == ["abcde", "defgh", "ghij"]
