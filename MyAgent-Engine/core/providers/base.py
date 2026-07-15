from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class ProviderChunk:
    """One provider stream event; the final event carries usage when available."""

    text: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    done: bool = False


@dataclass(frozen=True)
class RoutedProviderChunk:
    text: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    done: bool = False


class AIProvider(Protocol):
    name: str
    model: str
    configured: bool

    async def chat(self, messages: list[ProviderMessage]) -> ProviderResponse: ...
    def stream(self, messages: list[ProviderMessage]) -> AsyncIterator[ProviderChunk]: ...
    async def health(self) -> bool: ...
