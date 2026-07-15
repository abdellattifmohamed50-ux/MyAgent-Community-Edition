from __future__ import annotations

from collections.abc import AsyncIterator

from core.providers.base import ProviderMessage, ProviderResponse, RoutedProviderChunk
from core.providers.router import ProviderRouter


class ConversationalAgent:
    """Stateless cloud-brain orchestrator; persistence stays in application services."""

    name = "conversation"

    def __init__(self, providers: ProviderRouter) -> None:
        self.providers = providers

    async def reply(
        self,
        messages: list[ProviderMessage],
        provider: str | None = None,
    ) -> ProviderResponse:
        return await self.providers.chat(messages, provider)

    async def stream(
        self,
        messages: list[ProviderMessage],
        provider: str | None = None,
    ) -> AsyncIterator[RoutedProviderChunk]:
        async for chunk in self.providers.stream(messages, provider):
            yield chunk
