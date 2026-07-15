from __future__ import annotations

from collections.abc import AsyncIterator

from core.providers.base import ProviderChunk, ProviderMessage, ProviderResponse


class MockProvider:
    """Deterministic offline provider used for tests and first-run demos."""

    name = "mock"
    model = "myagent-demo"
    configured = True

    async def chat(self, messages: list[ProviderMessage]) -> ProviderResponse:
        user_text = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return ProviderResponse(
            text=(
                "MyAgent demo mode is active. Configure an AI provider key to receive "
                f"a live model response. Your message was: {user_text}"
            ),
            provider=self.name,
            model=self.model,
        )

    async def stream(self, messages: list[ProviderMessage]) -> AsyncIterator[ProviderChunk]:
        response = await self.chat(messages)
        for part in response.text.split(" "):
            yield ProviderChunk(text=part + " ")
        yield ProviderChunk(done=True)

    async def health(self) -> bool:
        return True
