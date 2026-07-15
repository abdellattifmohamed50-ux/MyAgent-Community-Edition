from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from apps.backend.api.errors import install_exception_handlers
from apps.backend.api.middleware import install_middleware
from apps.backend.api.routes import (
    auth,
    chat,
    conversations,
    health,
    knowledge,
    projects,
    providers,
    tools,
    websocket,
)
from core.config.settings import Settings, get_settings
from core.container import ApplicationContainer
from core.logging.logger import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    configure_logging(runtime_settings.log_level)
    container = ApplicationContainer.build(runtime_settings)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        del application
        await container.start()
        try:
            yield
        finally:
            await container.close()

    application = FastAPI(
        title=runtime_settings.app_name,
        version=runtime_settings.app_version,
        description=("Simple, modular AI agent backend for web, mobile and desktop clients."),
        lifespan=lifespan,
        docs_url="/docs" if runtime_settings.environment != "production" else None,
        redoc_url="/redoc" if runtime_settings.environment != "production" else None,
    )
    application.state.container = container
    application.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.cors_origin_list,
        allow_credentials="*" not in runtime_settings.cors_origin_list,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=runtime_settings.trusted_host_list,
    )
    install_middleware(application, runtime_settings)
    install_exception_handlers(application)
    routers = [
        health.router,
        auth.router,
        chat.router,
        conversations.router,
        projects.router,
        knowledge.router,
        providers.router,
        tools.router,
        websocket.router,
    ]
    for router in routers:
        application.include_router(router, prefix=runtime_settings.api_prefix)
        if runtime_settings.enable_legacy_routes:
            application.include_router(router, include_in_schema=False)
    return application


app = create_app()
