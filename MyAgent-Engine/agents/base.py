from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from core.providers.base import ProviderMessage, ProviderResponse, RoutedProviderChunk


class Agent(Protocol):
    """Small extension contract for independently testable MyAgent agents."""

    name: str

    async def reply(
        self,
        messages: list[ProviderMessage],
        provider: str | None = None,
    ) -> ProviderResponse: ...

    def stream(
        self,
        messages: list[ProviderMessage],
        provider: str | None = None,
    ) -> AsyncIterator[RoutedProviderChunk]: ...
