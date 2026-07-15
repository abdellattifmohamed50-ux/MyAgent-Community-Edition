from __future__ import annotations

import json

import httpx
import pytest

from core.exceptions.base import ProviderError, ProviderRequestError
from core.providers.base import ProviderMessage
from core.providers.http_providers import (
    AnthropicProvider,
    GeminiProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    OpenAIResponsesProvider,
)

MESSAGES = [ProviderMessage(role="user", content="Hello")]


@pytest.mark.asyncio
async def test_openai_responses_chat_is_private_and_tracks_usage() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            assert request.url.path == "/v1/models/gpt-5.6"
            assert request.headers["authorization"] == "Bearer test-key"
            return httpx.Response(200, json={"id": "gpt-5.6"})
        payload = json.loads(request.content)
        assert payload["store"] is False
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "model": "gpt-test",
                "output_text": "answer",
                "usage": {"input_tokens": 4, "output_tokens": 2},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
        provider = OpenAIResponsesProvider(
            "test-key", "gpt-5.6", "https://openai.test/v1", 10, client
        )
        response = await provider.chat(MESSAGES)
        healthy = await provider.health()
    assert response.text == "answer"
    assert (response.input_tokens, response.output_tokens) == (4, 2)
    assert healthy is True


@pytest.mark.asyncio
async def test_openai_responses_native_stream_parses_delta_and_usage() -> None:
    body = "\n".join(
        [
            'data: {"type":"response.output_text.delta","delta":"Hel"}',
            "",
            'data: {"type":"response.output_text.delta","delta":"lo"}',
            "",
            (
                'data: {"type":"response.completed","response":'
                '{"usage":{"input_tokens":3,"output_tokens":1}}}'
            ),
            "",
            "data: [DONE]",
            "",
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["stream"] is True
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
        provider = OpenAIResponsesProvider(
            "test-key", "gpt-test", "https://openai.test/v1", 10, client
        )
        chunks = [chunk async for chunk in provider.stream(MESSAGES)]
    assert "".join(chunk.text for chunk in chunks) == "Hello"
    assert chunks[-1].done is True
    assert (chunks[-1].input_tokens, chunks[-1].output_tokens) == (3, 1)


@pytest.mark.asyncio
async def test_openai_compatible_native_stream() -> None:
    body = (
        'data: {"choices":[{"delta":{"content":"Hi"}}]}\n\n'
        'data: {"choices":[],"usage":{"prompt_tokens":2,"completion_tokens":1}}\n\n'
        "data: [DONE]\n\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["stream_options"] == {"include_usage": True}
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
        provider = OpenAICompatibleProvider(
            name="openrouter",
            api_key="test-key",
            model="test-model",
            base_url="https://openrouter.test/api/v1",
            timeout=10,
            client=client,
            include_stream_usage=True,
        )
        chunks = [chunk async for chunk in provider.stream(MESSAGES)]
    assert "".join(chunk.text for chunk in chunks) == "Hi"
    assert chunks[-1].input_tokens == 2


@pytest.mark.asyncio
async def test_gemini_uses_header_instead_of_query_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "key=" not in str(request.url)
        assert request.headers["x-goog-api-key"] == "secret"
        if request.method == "GET":
            assert request.url.path.endswith("/models/gemini-test")
            return httpx.Response(200, json={"name": "models/gemini-test"})
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "Gemini"}]}}],
                "usageMetadata": {"promptTokenCount": 2, "candidatesTokenCount": 1},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
        provider = GeminiProvider("secret", "gemini-test", 10, client)
        response = await provider.chat(MESSAGES)
        healthy = await provider.health()
    assert response.text == "Gemini"
    assert healthy is True


@pytest.mark.asyncio
async def test_ollama_native_stream_reads_json_lines() -> None:
    body = (
        '{"message":{"content":"Lo"},"done":false}\n'
        '{"message":{"content":"cal"},"done":true,'
        '"prompt_eval_count":2,"eval_count":1}\n'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=body, headers={"content-type": "application/x-ndjson"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
        provider = OllamaProvider("http://ollama.test", "local", 10, client)
        chunks = [chunk async for chunk in provider.stream(MESSAGES)]
    assert "".join(chunk.text for chunk in chunks) == "Local"
    assert chunks[-1].output_tokens == 1


@pytest.mark.asyncio
async def test_openai_compatible_chat_supports_structured_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer key"
        return httpx.Response(
            200,
            json={
                "model": "compatible-test",
                "choices": [{"message": {"content": [{"text": "Part A"}, {"text": " + B"}]}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 2},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
        provider = OpenAICompatibleProvider(
            name="compatible",
            api_key="key",
            model="compatible-test",
            base_url="https://compatible.test/v1",
            timeout=10,
            client=client,
        )
        response = await provider.chat(MESSAGES)
    assert response.text == "Part A + B"
    assert (response.input_tokens, response.output_tokens) == (5, 2)


@pytest.mark.asyncio
async def test_anthropic_chat_and_compatibility_stream() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            assert request.url.path == "/v1/models/claude-test"
            assert request.headers["x-api-key"] == "key"
            return httpx.Response(200, json={"id": "claude-test"})
        payload = json.loads(request.content)
        assert payload["system"] == "Stay concise"
        return httpx.Response(
            200,
            json={
                "model": "claude-test",
                "content": [{"text": "A" * 60}],
                "usage": {"input_tokens": 3, "output_tokens": 4},
            },
        )

    messages = [
        ProviderMessage(role="system", content="Stay concise"),
        ProviderMessage(role="user", content="Hello"),
    ]
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
        provider = AnthropicProvider("key", "claude-test", 10, client)
        chunks = [chunk async for chunk in provider.stream(messages)]
        healthy = await provider.health()
    assert "".join(chunk.text for chunk in chunks) == "A" * 60
    assert chunks[-1].done is True
    assert chunks[-1].output_tokens == 4
    assert healthy is True


@pytest.mark.asyncio
async def test_gemini_native_stream_tracks_usage() -> None:
    body = (
        'data: {"candidates":[{"content":{"parts":[{"text":"Gem"}]}}]}\n\n'
        'data: {"candidates":[{"content":{"parts":[{"text":"ini"}]}}],'
        '"usageMetadata":{"promptTokenCount":4,"candidatesTokenCount":2}}\n\n'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-goog-api-key"] == "secret"
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
        chunks = [
            chunk
            async for chunk in GeminiProvider("secret", "gemini-test", 10, client).stream(MESSAGES)
        ]
    assert "".join(chunk.text for chunk in chunks) == "Gemini"
    assert (chunks[-1].input_tokens, chunks[-1].output_tokens) == (4, 2)


@pytest.mark.asyncio
async def test_ollama_chat_and_health() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": []})
        return httpx.Response(
            200,
            json={
                "model": "local",
                "message": {"content": "Local answer"},
                "prompt_eval_count": 3,
                "eval_count": 2,
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
        provider = OllamaProvider("http://ollama.test", "local", 10, client)
        response = await provider.chat(MESSAGES)
        healthy = await provider.health()
    assert response.text == "Local answer"
    assert healthy is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "retryable"),
    [(400, False), (429, True), (503, True)],
)
async def test_http_status_failures_are_classified(status_code: int, retryable: bool) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
        provider = OpenAICompatibleProvider(
            name="compatible",
            api_key="key",
            model="test",
            base_url="https://compatible.test/v1",
            timeout=10,
            client=client,
        )
        with pytest.raises(ProviderRequestError) as caught:
            await provider.chat(MESSAGES)
    assert getattr(caught.value, "retryable", None) is retryable


@pytest.mark.asyncio
async def test_malformed_usage_does_not_crash_a_valid_provider_reply() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "answer"}}],
                "usage": "not-an-object",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
        provider = OpenAICompatibleProvider(
            name="compatible",
            api_key="key",
            model="test",
            base_url="https://compatible.test/v1",
            timeout=10,
            client=client,
        )
        response = await provider.chat(MESSAGES)
    assert response.text == "answer"
    assert (response.input_tokens, response.output_tokens) == (0, 0)


@pytest.mark.asyncio
async def test_malformed_choices_are_reported_as_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": ["invalid"]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
        provider = OpenAICompatibleProvider(
            name="compatible",
            api_key="key",
            model="test",
            base_url="https://compatible.test/v1",
            timeout=10,
            client=client,
        )
        with pytest.raises(ProviderError, match="returned no choices"):
            await provider.chat(MESSAGES)


@pytest.mark.asyncio
async def test_compatible_provider_health_checks_the_authenticated_models_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/models"
        assert request.headers["authorization"] == "Bearer key"
        return httpx.Response(200, json={"data": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
        provider = OpenAICompatibleProvider(
            name="compatible",
            api_key="key",
            model="test",
            base_url="https://compatible.test/v1",
            timeout=10,
            client=client,
        )
        assert await provider.health() is True


@pytest.mark.asyncio
async def test_provider_health_returns_false_for_network_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
        provider = OpenAICompatibleProvider(
            name="compatible",
            api_key="key",
            model="test",
            base_url="https://compatible.test/v1",
            timeout=10,
            client=client,
        )
        assert await provider.health() is False
