from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import quote

import httpx

from core.exceptions.base import ProviderError, ProviderRequestError
from core.providers.base import ProviderChunk, ProviderMessage, ProviderResponse
from core.providers.client import LazyAsyncClient

HttpClient = httpx.AsyncClient | LazyAsyncClient


class HttpProvider(ABC):
    name: str
    model: str
    configured: bool

    def __init__(self, client: HttpClient, *, timeout: float = 60.0) -> None:
        self.client = client
        self.timeout = timeout

    @abstractmethod
    async def chat(self, messages: list[ProviderMessage]) -> ProviderResponse:
        """Return a complete provider response."""

    async def stream(self, messages: list[ProviderMessage]) -> AsyncIterator[ProviderChunk]:
        """Compatibility stream for providers without a native stream implementation."""
        response = await self.chat(messages)
        for index in range(0, len(response.text), 48):
            yield ProviderChunk(text=response.text[index : index + 48])
        yield ProviderChunk(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            done=True,
        )

    async def health(self) -> bool:
        return self.configured


class OpenAIResponsesProvider(HttpProvider):
    name = "openai"

    def __init__(
        self,
        api_key: str | None,
        model: str,
        base_url: str,
        timeout: float,
        client: HttpClient,
    ) -> None:
        super().__init__(client, timeout=timeout)
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.configured = bool(api_key)

    def _payload(self, messages: list[ProviderMessage]) -> dict[str, Any]:
        return {
            "model": self.model,
            "input": [{"role": item.role, "content": item.content} for item in messages],
            "store": False,
        }

    async def chat(self, messages: list[ProviderMessage]) -> ProviderResponse:
        headers = self._headers()
        data = await _post_json(
            self.client,
            f"{self.base_url}/responses",
            self._payload(messages),
            headers,
            self.timeout,
        )
        usage = _mapping(data.get("usage"))
        return ProviderResponse(
            text=_openai_response_text(data),
            provider=self.name,
            model=str(data.get("model", self.model)),
            input_tokens=_token_count(usage.get("input_tokens")),
            output_tokens=_token_count(usage.get("output_tokens")),
        )

    async def stream(self, messages: list[ProviderMessage]) -> AsyncIterator[ProviderChunk]:
        payload = {**self._payload(messages), "stream": True}
        input_tokens = 0
        output_tokens = 0
        async for event in _stream_sse_json(
            self.client,
            f"{self.base_url}/responses",
            payload,
            self._headers(),
            self.timeout,
        ):
            event_type = event.get("type")
            if event_type == "response.output_text.delta":
                delta = event.get("delta")
                if isinstance(delta, str) and delta:
                    yield ProviderChunk(text=delta)
            elif event_type == "response.completed":
                response = _mapping(event.get("response"))
                usage = _mapping(response.get("usage"))
                input_tokens = _token_count(usage.get("input_tokens"))
                output_tokens = _token_count(usage.get("output_tokens"))
            elif event_type in {"error", "response.failed"}:
                raise ProviderRequestError("OpenAI stream failed", retryable=False)
        yield ProviderChunk(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            done=True,
        )

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ProviderError("OpenAI is not configured")
        return {"Authorization": f"Bearer {self.api_key}"}

    async def health(self) -> bool:
        if not self.configured:
            return False
        return await _get_health(
            self.client,
            f"{self.base_url}/models/{quote(self.model, safe='')}",
            self._headers(),
        )


class OpenAICompatibleProvider(HttpProvider):
    def __init__(
        self,
        *,
        name: str,
        api_key: str | None,
        model: str,
        base_url: str,
        timeout: float,
        client: HttpClient,
        extra_headers: dict[str, str] | None = None,
        include_stream_usage: bool = False,
    ) -> None:
        super().__init__(client, timeout=timeout)
        self.name = name
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.configured = bool(api_key)
        self.extra_headers = extra_headers or {}
        self.include_stream_usage = include_stream_usage

    def _payload(self, messages: list[ProviderMessage]) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [{"role": item.role, "content": item.content} for item in messages],
        }

    async def chat(self, messages: list[ProviderMessage]) -> ProviderResponse:
        data = await _post_json(
            self.client,
            f"{self.base_url}/chat/completions",
            self._payload(messages),
            self._headers(),
            self.timeout,
        )
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ProviderError(f"{self.name} returned no choices")
        content = _mapping(choices[0].get("message")).get("content", "")
        usage = _mapping(data.get("usage"))
        return ProviderResponse(
            text=_content_text(content),
            provider=self.name,
            model=str(data.get("model", self.model)),
            input_tokens=_token_count(usage.get("prompt_tokens")),
            output_tokens=_token_count(usage.get("completion_tokens")),
        )

    async def stream(self, messages: list[ProviderMessage]) -> AsyncIterator[ProviderChunk]:
        payload = {**self._payload(messages), "stream": True}
        if self.include_stream_usage:
            payload["stream_options"] = {"include_usage": True}
        input_tokens = 0
        output_tokens = 0
        async for event in _stream_sse_json(
            self.client,
            f"{self.base_url}/chat/completions",
            payload,
            self._headers(),
            self.timeout,
        ):
            usage = _mapping(event.get("usage"))
            input_tokens = _token_count(usage.get("prompt_tokens"), input_tokens)
            output_tokens = _token_count(usage.get("completion_tokens"), output_tokens)
            choices = event.get("choices")
            if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                content = _mapping(choices[0].get("delta")).get("content", "")
                text = _content_text(content)
                if text:
                    yield ProviderChunk(text=text)
        yield ProviderChunk(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            done=True,
        )

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ProviderError(f"{self.name} is not configured")
        return {"Authorization": f"Bearer {self.api_key}", **self.extra_headers}

    async def health(self) -> bool:
        if not self.configured:
            return False
        return await _get_health(
            self.client,
            f"{self.base_url}/models",
            self._headers(),
        )


class GeminiProvider(HttpProvider):
    name = "gemini"

    def __init__(
        self,
        api_key: str | None,
        model: str,
        timeout: float,
        client: HttpClient,
    ) -> None:
        super().__init__(client, timeout=timeout)
        self.api_key = api_key
        self.model = model
        self.configured = bool(api_key)

    def _payload(self, messages: list[ProviderMessage]) -> dict[str, Any]:
        system = "\n".join(item.content for item in messages if item.role == "system")
        contents = [
            {
                "role": "model" if item.role == "assistant" else "user",
                "parts": [{"text": item.content}],
            }
            for item in messages
            if item.role != "system"
        ]
        payload: dict[str, Any] = {"contents": contents}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        return payload

    async def chat(self, messages: list[ProviderMessage]) -> ProviderResponse:
        data = await _post_json(
            self.client,
            self._url("generateContent"),
            self._payload(messages),
            self._headers(),
            self.timeout,
        )
        usage = _mapping(data.get("usageMetadata"))
        return ProviderResponse(
            text=_gemini_text(data),
            provider=self.name,
            model=self.model,
            input_tokens=_token_count(usage.get("promptTokenCount")),
            output_tokens=_token_count(usage.get("candidatesTokenCount")),
        )

    async def stream(self, messages: list[ProviderMessage]) -> AsyncIterator[ProviderChunk]:
        input_tokens = 0
        output_tokens = 0
        async for event in _stream_sse_json(
            self.client,
            self._url("streamGenerateContent") + "?alt=sse",
            self._payload(messages),
            self._headers(),
            self.timeout,
        ):
            text = _gemini_text(event, required=False)
            if text:
                yield ProviderChunk(text=text)
            usage = _mapping(event.get("usageMetadata"))
            input_tokens = _token_count(usage.get("promptTokenCount"), input_tokens)
            output_tokens = _token_count(usage.get("candidatesTokenCount"), output_tokens)
        yield ProviderChunk(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            done=True,
        )

    def _url(self, method: str) -> str:
        return f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:{method}"

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ProviderError("Gemini is not configured")
        return {"x-goog-api-key": self.api_key}

    async def health(self) -> bool:
        if not self.configured:
            return False
        model = quote(self.model.removeprefix("models/"), safe="")
        return await _get_health(
            self.client,
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}",
            self._headers(),
        )


class AnthropicProvider(HttpProvider):
    name = "anthropic"

    def __init__(
        self,
        api_key: str | None,
        model: str,
        timeout: float,
        client: HttpClient,
    ) -> None:
        super().__init__(client, timeout=timeout)
        self.api_key = api_key
        self.model = model
        self.configured = bool(api_key)

    async def chat(self, messages: list[ProviderMessage]) -> ProviderResponse:
        if not self.api_key:
            raise ProviderError("Anthropic is not configured")
        system = "\n".join(item.content for item in messages if item.role == "system")
        data = await _post_json(
            self.client,
            "https://api.anthropic.com/v1/messages",
            {
                "model": self.model,
                "max_tokens": 4096,
                "system": system,
                "messages": [
                    {"role": item.role, "content": item.content}
                    for item in messages
                    if item.role in {"user", "assistant"}
                ],
            },
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            self.timeout,
        )
        content = data.get("content")
        if not isinstance(content, list):
            raise ProviderError("Anthropic returned invalid content")
        usage = _mapping(data.get("usage"))
        return ProviderResponse(
            text="".join(str(item.get("text", "")) for item in content if isinstance(item, dict)),
            provider=self.name,
            model=str(data.get("model", self.model)),
            input_tokens=_token_count(usage.get("input_tokens")),
            output_tokens=_token_count(usage.get("output_tokens")),
        )

    async def health(self) -> bool:
        if not self.configured or not self.api_key:
            return False
        return await _get_health(
            self.client,
            f"https://api.anthropic.com/v1/models/{quote(self.model, safe='')}",
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
        )


class OllamaProvider(HttpProvider):
    name = "ollama"
    configured = True

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float,
        client: HttpClient,
    ) -> None:
        super().__init__(client, timeout=timeout)
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _payload(self, messages: list[ProviderMessage]) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [{"role": item.role, "content": item.content} for item in messages],
        }

    async def chat(self, messages: list[ProviderMessage]) -> ProviderResponse:
        data = await _post_json(
            self.client,
            f"{self.base_url}/api/chat",
            {**self._payload(messages), "stream": False},
            {},
            self.timeout,
        )
        message = _mapping(data.get("message"))
        return ProviderResponse(
            text=str(message.get("content", "")),
            provider=self.name,
            model=str(data.get("model", self.model)),
            input_tokens=_token_count(data.get("prompt_eval_count")),
            output_tokens=_token_count(data.get("eval_count")),
        )

    async def stream(self, messages: list[ProviderMessage]) -> AsyncIterator[ProviderChunk]:
        input_tokens = 0
        output_tokens = 0
        async for event in _stream_json_lines(
            self.client,
            f"{self.base_url}/api/chat",
            {**self._payload(messages), "stream": True},
            {},
            self.timeout,
        ):
            text = str(_mapping(event.get("message")).get("content", ""))
            if text:
                yield ProviderChunk(text=text)
            if event.get("done") is True:
                input_tokens = _token_count(event.get("prompt_eval_count"))
                output_tokens = _token_count(event.get("eval_count"))
        yield ProviderChunk(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            done=True,
        )

    async def health(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/api/tags", timeout=2.0)
            return response.is_success
        except httpx.HTTPError:
            return False


async def _post_json(
    client: HttpClient,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
) -> dict[str, Any]:
    try:
        response = await client.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json", **headers},
            timeout=timeout,
        )
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise ProviderRequestError("Provider returned invalid JSON", retryable=False)
        return result
    except ProviderRequestError:
        raise
    except httpx.HTTPStatusError as exc:
        raise _status_error(exc) from exc
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        raise ProviderRequestError("Provider network request failed", retryable=True) from exc
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        raise ProviderRequestError("Provider response was invalid", retryable=False) from exc


async def _get_health(
    client: HttpClient,
    url: str,
    headers: dict[str, str],
) -> bool:
    try:
        response = await client.get(url, headers=headers, timeout=2.0)
        return response.is_success
    except httpx.HTTPError:
        return False


async def _stream_sse_json(
    client: HttpClient,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
) -> AsyncIterator[dict[str, Any]]:
    try:
        async with client.stream(
            "POST",
            url,
            json=payload,
            headers={"Accept": "text/event-stream", "Content-Type": "application/json", **headers},
            timeout=timeout,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if not data or data == "[DONE]":
                    continue
                event = json.loads(data)
                if not isinstance(event, dict):
                    raise ProviderRequestError("Provider stream event was invalid", retryable=False)
                yield event
    except ProviderRequestError:
        raise
    except httpx.HTTPStatusError as exc:
        raise _status_error(exc) from exc
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        raise ProviderRequestError(
            "Provider stream network request failed", retryable=True
        ) from exc
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        raise ProviderRequestError("Provider stream was invalid", retryable=False) from exc


async def _stream_json_lines(
    client: HttpClient,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
) -> AsyncIterator[dict[str, Any]]:
    try:
        async with client.stream(
            "POST",
            url,
            json=payload,
            headers={"Content-Type": "application/json", **headers},
            timeout=timeout,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                event = json.loads(line)
                if not isinstance(event, dict):
                    raise ProviderRequestError("Provider stream event was invalid", retryable=False)
                yield event
    except ProviderRequestError:
        raise
    except httpx.HTTPStatusError as exc:
        raise _status_error(exc) from exc
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        raise ProviderRequestError(
            "Provider stream network request failed", retryable=True
        ) from exc
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        raise ProviderRequestError("Provider stream was invalid", retryable=False) from exc


def _status_error(exc: httpx.HTTPStatusError) -> ProviderRequestError:
    status = exc.response.status_code
    retryable = status in {408, 409, 425, 429} or status >= 500
    return ProviderRequestError(f"Provider returned HTTP {status}", retryable=retryable)


def _content_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
    return str(content) if content is not None else ""


def _gemini_text(data: dict[str, Any], *, required: bool = True) -> str:
    try:
        return "".join(
            str(part.get("text", "")) for part in data["candidates"][0]["content"]["parts"]
        )
    except (AttributeError, KeyError, IndexError, TypeError) as exc:
        if required:
            raise ProviderError("Gemini returned an invalid response") from exc
        return ""


def _openai_response_text(data: dict[str, Any]) -> str:
    if isinstance(data.get("output_text"), str):
        return str(data["output_text"])
    parts: list[str] = []
    output = data.get("output")
    if not isinstance(output, list):
        output = []
    for item in output:
        if not isinstance(item, dict):
            continue
        content_items = item.get("content")
        if not isinstance(content_items, list):
            continue
        for content in content_items:
            if not isinstance(content, dict):
                continue
            if content.get("type") == "output_text":
                parts.append(str(content.get("text", "")))
    if not parts:
        raise ProviderError("OpenAI returned no output text")
    return "".join(parts)


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _token_count(value: object, fallback: int = 0) -> int:
    if isinstance(value, bool):
        return fallback
    if isinstance(value, int):
        count = value
    elif isinstance(value, str):
        try:
            count = int(value)
        except ValueError:
            return fallback
    else:
        return fallback
    return count if count >= 0 else fallback
