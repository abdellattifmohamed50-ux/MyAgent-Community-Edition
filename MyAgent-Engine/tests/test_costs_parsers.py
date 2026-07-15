from __future__ import annotations

import pytest

from core.exceptions.base import ValidationError
from core.providers.costs import UsageCostEstimator
from core.rag.parsers import DocumentParser
from core.rag.search import BM25Lite


def test_usage_cost_estimator_uses_exact_model_then_provider_fallback() -> None:
    estimator = UsageCostEstimator(
        {
            "openai": {"input": 1.0, "output": 2.0},
            "openai:premium": {"input": 3.0, "output": 4.0},
        }
    )
    assert estimator.estimate_microusd("openai", "premium", 10, 5) == 50
    assert estimator.estimate_microusd("openai", "other", 10, 5) == 20
    assert estimator.estimate_microusd("gemini", "model", 10, 5) is None


def test_document_parser_accepts_valid_json_and_rejects_binary() -> None:
    parser = DocumentParser()
    parsed = parser.parse_upload("../facts.json", "application/json", b'{"ok": true}')
    assert parsed.title == "facts.json"
    assert '"ok": true' in parsed.content
    with pytest.raises(ValidationError, match="binary"):
        parser.parse_upload("bad.txt", "text/plain", b"bad\x00data")


def test_unicode_ranker_normalizes_arabic_and_finds_relevant_excerpt() -> None:
    ranker = BM25Lite()
    assert ranker.score("إدارة المشاريع", "اداره المشاريع باحتراف") > 0
    assert ranker.candidate_terms("إدارة") == ["إدارة", "اداره"]
    document = "مقدمة غير مهمة. " * 100 + "هذا الجزء يشرح إدارة المشاريع بالتفصيل."
    excerpt = ranker.best_excerpt("إدارة المشاريع", document, 240)
    assert "إدارة المشاريع" in excerpt
