from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from core.exceptions.base import ProviderError, ProviderRequestError
from core.logging.logger import get_logger
from core.providers.base import (
    AIProvider,
    ProviderMessage,
    ProviderResponse,
    RoutedProviderChunk,
)
from core.providers.registry import ProviderRegistry

logger = get_logger(__name__)


class ProviderRouter:
    """Selects a provider, retries transient failures and falls back safely."""

    def __init__(
        self,
        registry: ProviderRegistry,
        default_provider: str = "mock",
        retry_count: int = 2,
        fallback_names: list[str] | None = None,
        retry_base_seconds: float = 0.25,
    ) -> None:
        self.registry = registry
        self.default_provider = default_provider
        self.retry_count = max(0, retry_count)
        self.fallback_names = fallback_names or ["mock"]
        self.retry_base_seconds = max(0.0, retry_base_seconds)

    def candidates(self, requested: str | None) -> list[AIProvider]:
        ordered_names = [requested] if requested else [self.default_provider, *self.fallback_names]
        seen: set[str] = set()
        providers: list[AIProvider] = []
        for name in ordered_names:
            if name in seen:
                continue
            seen.add(name)
            try:
                provider = self.registry.get(name)
            except ProviderError:
                if requested == name:
                    raise
                continue
            if provider.configured:
                providers.append(provider)
            elif requested == name:
                raise ProviderError(f"Provider is not configured: {name}")
        if not providers:
            raise ProviderError("No configured provider is available")
        return providers

    async def chat(
        self,
        messages: list[ProviderMessage],
        provider_name: str | None = None,
    ) -> ProviderResponse:
        errors: list[str] = []
        for provider in self.candidates(provider_name):
            for attempt in range(self.retry_count + 1):
                try:
                    return await provider.chat(messages)
                except ProviderRequestError as exc:
                    errors.append(f"{provider.name}: {type(exc).__name__}")
                    logger.warning(
                        "provider_request_failed",
                        extra={"provider": provider.name, "retryable": exc.retryable},
                    )
                    if exc.retryable and attempt < self.retry_count:
                        await asyncio.sleep(self.retry_base_seconds * (2**attempt))
                        continue
                    break
                except ProviderError as exc:
                    errors.append(f"{provider.name}: {type(exc).__name__}")
                    break
            if provider_name is not None:
                break
        raise ProviderError("All configured providers failed: " + ", ".join(errors))

    async def stream(
        self,
        messages: list[ProviderMessage],
        provider_name: str | None = None,
    ) -> AsyncIterator[RoutedProviderChunk]:
        errors: list[str] = []
        for provider in self.candidates(provider_name):
            emitted = False
            for attempt in range(self.retry_count + 1):
                try:
                    async for chunk in provider.stream(messages):
                        emitted = emitted or bool(chunk.text)
                        yield RoutedProviderChunk(
                            text=chunk.text,
                            provider=provider.name,
                            model=provider.model,
                            input_tokens=chunk.input_tokens,
                            output_tokens=chunk.output_tokens,
                            done=chunk.done,
                        )
                    return
                except ProviderRequestError as exc:
                    errors.append(f"{provider.name}: {type(exc).__name__}")
                    if emitted:
                        raise ProviderError(
                            f"Provider {provider.name} stream was interrupted"
                        ) from exc
                    if exc.retryable and attempt < self.retry_count:
                        await asyncio.sleep(self.retry_base_seconds * (2**attempt))
                        continue
                    break
                except ProviderError as exc:
                    errors.append(f"{provider.name}: {type(exc).__name__}")
                    if emitted or provider_name is not None:
                        raise ProviderError(f"Provider {provider.name} stream failed") from exc
                    break
            if provider_name is not None:
                break
        raise ProviderError("All configured provider streams failed: " + ", ".join(errors))
