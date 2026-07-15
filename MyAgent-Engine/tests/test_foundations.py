from __future__ import annotations

import logging

import pytest

from core.exceptions.base import AuthorizationError, RateLimitError, ValidationError
from core.logging.logger import SensitiveQueryFilter
from core.rag.chunking import chunk_text
from core.security.input_validation import validate_chat_input
from core.security.rate_limiter import InMemoryRateLimiter
from core.security.rbac import Role, require_role


def test_chunking_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError, match="larger than overlap"):
        chunk_text("content", chunk_size=5, overlap=5)


def test_chunking_empty_text_returns_no_chunks() -> None:
    assert chunk_text("") == []


def test_rate_limiter_blocks_excess_requests() -> None:
    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60)
    limiter.check("client")
    with pytest.raises(RateLimitError):
        limiter.check("client")


def test_rate_limiter_expires_old_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    times = iter([1.0, 10.0])
    monkeypatch.setattr("core.security.rate_limiter.time.monotonic", lambda: next(times))
    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=5)
    limiter.check("client")
    limiter.check("client")
    assert list(limiter._requests["client"]) == [10.0]


def test_rate_limiter_bounds_client_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    times = iter([1.0, 2.0, 20.0])
    monkeypatch.setattr("core.security.rate_limiter.time.monotonic", lambda: next(times))
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=10, max_keys=1)
    limiter.check("first")
    limiter.check("second")
    assert "first" not in limiter._requests
    limiter.check("third")
    assert list(limiter._requests) == ["third"]


def test_rate_limiter_periodically_cleans_stale_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("core.security.rate_limiter.time.monotonic", lambda: 100.0)
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=10)
    limiter._checks = 999
    limiter._requests["stale"].append(1.0)
    limiter.check("current")
    assert "stale" not in limiter._requests


def test_admin_satisfies_user_role() -> None:
    require_role(["admin"], Role.USER)


def test_user_cannot_satisfy_admin_role() -> None:
    with pytest.raises(AuthorizationError):
        require_role(["user"], Role.ADMIN)


def test_chat_input_is_trimmed_and_empty_rejected() -> None:
    assert validate_chat_input("  hello  ") == "hello"
    with pytest.raises(ValidationError):
        validate_chat_input("   ")


def test_access_log_filter_redacts_query_credentials() -> None:
    record = logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        __file__,
        1,
        '%s - "WebSocket %s" [accepted]',
        ("127.0.0.1", "/api/v1/ws/chat?token=secret.jwt&mode=chat"),
        None,
    )
    assert SensitiveQueryFilter().filter(record) is True
    rendered = record.getMessage()
    assert "secret.jwt" not in rendered
    assert "token=[REDACTED]" in rendered
