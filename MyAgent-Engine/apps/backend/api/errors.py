from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from core.exceptions.base import (
    AuthenticationError,
    AuthorizationError,
    MyAgentError,
    ProviderError,
    RateLimitError,
    ValidationError,
)
from core.logging.logger import get_logger, request_id_ctx

logger = get_logger(__name__)


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(MyAgentError)
    async def handle_domain_error(request: Request, exc: MyAgentError) -> JSONResponse:
        del request
        status = 400
        if isinstance(exc, AuthenticationError):
            status = 401
        elif isinstance(exc, AuthorizationError):
            status = 403
        elif isinstance(exc, RateLimitError):
            status = 429
        elif isinstance(exc, ProviderError):
            status = 502
        elif isinstance(exc, ValidationError):
            status = 422
        return JSONResponse(
            status_code=status,
            content={
                "error": type(exc).__name__,
                "message": str(exc),
                "request_id": request_id_ctx.get(),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        del request
        details = [
            {
                "type": error.get("type", "validation_error"),
                "location": list(error.get("loc", ())),
                "message": error.get("msg", "Invalid value"),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": "RequestValidationError",
                "message": "Request data is invalid",
                "details": details,
                "request_id": request_id_ctx.get(),
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        del request
        logger.exception("unhandled_request_error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "The request could not be completed",
                "request_id": request_id_ctx.get(),
            },
        )
