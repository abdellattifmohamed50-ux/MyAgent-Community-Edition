from __future__ import annotations

import time
from collections import defaultdict, deque

from core.exceptions.base import RateLimitError


class InMemoryRateLimiter:
    """Bounded single-process sliding-window limiter for the Community Edition monolith."""

    def __init__(self, max_requests: int, window_seconds: int, max_keys: int = 20_000) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._checks = 0

    def check(self, key: str) -> None:
        now = time.monotonic()
        self._checks += 1
        if self._checks % 1_000 == 0:
            self._remove_stale(now)
        if key not in self._requests and len(self._requests) >= self.max_keys:
            self._remove_stale(now)
            if len(self._requests) >= self.max_keys:
                oldest = min(self._requests, key=lambda item: self._requests[item][-1])
                self._requests.pop(oldest, None)
        bucket = self._requests[key]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            raise RateLimitError("Rate limit exceeded")
        bucket.append(now)

    def _remove_stale(self, now: float) -> None:
        stale = [
            key
            for key, bucket in self._requests.items()
            if not bucket or now - bucket[-1] > self.window_seconds
        ]
        for key in stale:
            self._requests.pop(key, None)
