import pytest

from core.exceptions.base import ProviderError, ProviderRequestError
from core.providers.base import ProviderChunk, ProviderMessage, ProviderResponse
from core.providers.mock import MockProvider
from core.providers.registry import ProviderRegistry
from core.providers.router import ProviderRouter


@pytest.mark.asyncio
async def test_mock_provider_chat() -> None:
    provider = MockProvider()
    response = await provider.chat([ProviderMessage(role="user", content="hello")])
    assert "hello" in response.text


@pytest.mark.asyncio
async def test_router_rejects_unknown_explicit_provider() -> None:
    registry = ProviderRegistry()
    registry.register(MockProvider())
    router = ProviderRouter(registry)
    with pytest.raises(ProviderError, match="not registered"):
        await router.chat([ProviderMessage(role="user", content="hello")], "missing")


@pytest.mark.asyncio
async def test_mock_provider_streams_chunks() -> None:
    chunks = [
        chunk
        async for chunk in MockProvider().stream([ProviderMessage(role="user", content="hello")])
    ]
    assert "hello" in "".join(chunk.text for chunk in chunks)
    assert chunks[-1].done is True


class FailingProvider:
    name = "failing"
    model = "failure-model"
    configured = True

    def __init__(self, *, retryable: bool) -> None:
        self.retryable = retryable
        self.calls = 0

    async def chat(self, messages: list[ProviderMessage]) -> ProviderResponse:
        del messages
        self.calls += 1
        raise ProviderRequestError("failure", retryable=self.retryable)

    async def stream(self, messages: list[ProviderMessage]):  # type: ignore[no-untyped-def]
        del messages
        self.calls += 1
        if False:
            yield ProviderChunk()
        raise ProviderRequestError("failure", retryable=self.retryable)

    async def health(self) -> bool:
        return False


@pytest.mark.asyncio
async def test_router_retries_only_retryable_failures_then_falls_back() -> None:
    registry = ProviderRegistry()
    failing = FailingProvider(retryable=True)
    registry.register(failing)
    registry.register(MockProvider())
    router = ProviderRouter(
        registry,
        default_provider="failing",
        retry_count=2,
        retry_base_seconds=0,
        fallback_names=["mock"],
    )
    response = await router.chat([ProviderMessage(role="user", content="hello")])
    assert response.provider == "mock"
    assert failing.calls == 3


@pytest.mark.asyncio
async def test_explicit_provider_never_silently_falls_back() -> None:
    registry = ProviderRegistry()
    failing = FailingProvider(retryable=False)
    registry.register(failing)
    registry.register(MockProvider())
    router = ProviderRouter(registry, retry_count=3, fallback_names=["mock"])
    with pytest.raises(ProviderError, match="All configured providers failed"):
        await router.chat([ProviderMessage(role="user", content="hello")], "failing")
    assert failing.calls == 1


@pytest.mark.asyncio
async def test_stream_retries_before_emitting_then_falls_back() -> None:
    registry = ProviderRegistry()
    failing = FailingProvider(retryable=True)
    registry.register(failing)
    registry.register(MockProvider())
    router = ProviderRouter(
        registry,
        default_provider="failing",
        retry_count=1,
        retry_base_seconds=0,
        fallback_names=["mock"],
    )
    chunks = [
        chunk async for chunk in router.stream([ProviderMessage(role="user", content="hello")])
    ]
    assert "hello" in "".join(chunk.text for chunk in chunks)
    assert all(chunk.provider == "mock" for chunk in chunks)
    assert failing.calls == 2


class InterruptedProvider(FailingProvider):
    async def stream(self, messages: list[ProviderMessage]):  # type: ignore[no-untyped-def]
        del messages
        yield ProviderChunk(text="partial")
        raise ProviderRequestError("interrupted", retryable=True)


@pytest.mark.asyncio
async def test_stream_never_mixes_providers_after_partial_output() -> None:
    registry = ProviderRegistry()
    registry.register(InterruptedProvider(retryable=True))
    registry.register(MockProvider())
    router = ProviderRouter(
        registry,
        default_provider="failing",
        fallback_names=["mock"],
        retry_base_seconds=0,
    )
    with pytest.raises(ProviderError, match="stream was interrupted"):
        async for _ in router.stream([ProviderMessage(role="user", content="hello")]):
            pass


def test_registry_rejects_duplicate_provider() -> None:
    registry = ProviderRegistry()
    registry.register(MockProvider())
    with pytest.raises(ProviderError, match="already registered"):
        registry.register(MockProvider())
