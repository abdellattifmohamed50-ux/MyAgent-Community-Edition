from __future__ import annotations

import re
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from core.config.settings import Settings
from core.exceptions.base import AuthenticationError, RateLimitError
from core.logging.logger import request_id_ctx
from core.security.jwt import TokenService
from core.security.rate_limiter import InMemoryRateLimiter


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        supplied = request.headers.get("x-request-id", "")[:128]
        request_id = supplied if re.fullmatch(r"[A-Za-z0-9._-]+", supplied) else uuid4().hex
        token = request_id_ctx.set(request_id)
        try:
            response = await call_next(request)
            response.headers["x-request-id"] = request_id
            return response
        finally:
            request_id_ctx.reset(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        response.headers["referrer-policy"] = "no-referrer"
        response.headers["permissions-policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["cross-origin-opener-policy"] = "same-origin"
        response.headers["x-permitted-cross-domain-policies"] = "none"
        if request.url.scheme == "https":
            response.headers["strict-transport-security"] = "max-age=31536000; includeSubDomains"
        if "/auth/" in request.url.path:
            response.headers["cache-control"] = "no-store"
        return response


class RequestSizeMiddleware:
    """Reject oversized HTTP bodies, including chunked requests without a length header."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        raw_length = headers.get(b"content-length")
        if raw_length is not None:
            try:
                declared_length = int(raw_length)
            except ValueError:
                await self._reject_invalid_length(scope, receive, send)
                return
            if declared_length < 0:
                await self._reject_invalid_length(scope, receive, send)
                return
            if declared_length > self.max_bytes:
                await self._reject(scope, receive, send)
                return
        received = 0
        buffered: list[Message] = []
        while True:
            message = await receive()
            buffered.append(message)
            if message["type"] != "http.request":
                break
            received += len(message.get("body", b""))
            if received > self.max_bytes:
                await self._reject(scope, receive, send)
                return
            if not message.get("more_body", False):
                break
        index = 0

        async def receive_buffered() -> Message:
            nonlocal index
            if index < len(buffered):
                message = buffered[index]
                index += 1
                return message
            return await receive()

        await self.app(scope, receive_buffered, send)

    @staticmethod
    async def _reject_invalid_length(scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            status_code=400,
            content={
                "error": "invalid_content_length",
                "message": "Content-Length must be a non-negative integer",
            },
        )
        await response(scope, receive, send)

    @staticmethod
    async def _reject(scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            status_code=413,
            content={"error": "request_too_large", "message": "Request body is too large"},
        )
        await response(scope, receive, send)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        limiter: InMemoryRateLimiter,
        auth_limiter: InMemoryRateLimiter,
        settings: Settings,
    ) -> None:
        super().__init__(app)
        self.limiter = limiter
        self.auth_limiter = auth_limiter
        self.tokens = TokenService(settings)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path.endswith("/health") or "/health/" in request.url.path:
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        sensitive_auth_path = request.url.path.endswith(("/auth/login", "/auth/register"))
        active_limiter = self.auth_limiter if sensitive_auth_path else self.limiter
        key = f"client:{client}"
        if not sensitive_auth_path:
            authorization = request.headers.get("authorization", "")
            if authorization.lower().startswith("bearer "):
                try:
                    payload = self.tokens.decode(
                        authorization.split(" ", 1)[1], expected_type="access"
                    )
                    key = f"user:{payload['sub']}"
                except AuthenticationError:
                    pass
        try:
            active_limiter.check(key)
        except RateLimitError:
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limit", "message": "Too many requests"},
                headers={"Retry-After": str(active_limiter.window_seconds)},
            )
        return await call_next(request)


def install_middleware(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestSizeMiddleware, max_bytes=settings.max_request_body_bytes)
    app.add_middleware(
        RateLimitMiddleware,
        limiter=InMemoryRateLimiter(
            settings.rate_limit_requests,
            settings.rate_limit_window_seconds,
        ),
        auth_limiter=InMemoryRateLimiter(
            settings.auth_rate_limit_requests,
            settings.rate_limit_window_seconds,
        ),
        settings=settings,
    )
    app.add_middleware(RequestIdMiddleware)
