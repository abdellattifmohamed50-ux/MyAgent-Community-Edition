from __future__ import annotations

from core.exceptions.base import ProviderError
from core.providers.base import AIProvider


class ProviderRegistry:
    """Runtime registry for AI providers."""

    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register(self, provider: AIProvider) -> None:
        if provider.name in self._providers:
            raise ProviderError(f"Provider already registered: {provider.name}")
        self._providers[provider.name] = provider

    def get(self, name: str) -> AIProvider:
        provider = self._providers.get(name)
        if provider is None:
            raise ProviderError(f"Provider not registered: {name}")
        return provider

    def names(self) -> list[str]:
        return sorted(self._providers)

    def all(self) -> list[AIProvider]:
        return [self._providers[name] for name in self.names()]
