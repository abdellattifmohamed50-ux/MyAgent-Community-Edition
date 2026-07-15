from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Any

import httpx


class LazyAsyncClient:
    """Creates the shared provider connection pool only on the first network call."""

    def __init__(
        self,
        *,
        timeout: httpx.Timeout,
        limits: httpx.Limits,
        headers: dict[str, str],
        trust_env: bool,
    ) -> None:
        self._timeout = timeout
        self._limits = limits
        self._headers = headers
        self._trust_env = trust_env
        self._client: httpx.AsyncClient | None = None

    def _get(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                limits=self._limits,
                headers=self._headers,
                trust_env=self._trust_env,
            )
        return self._client

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self._get().post(url, **kwargs)

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self._get().get(url, **kwargs)

    def stream(
        self, method: str, url: str, **kwargs: Any
    ) -> AbstractAsyncContextManager[httpx.Response]:
        return self._get().stream(method, url, **kwargs)

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
