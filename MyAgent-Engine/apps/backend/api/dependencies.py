from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated, TypedDict

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.settings import Settings
from core.container import ApplicationContainer
from core.exceptions.base import AuthenticationError
from core.security.jwt import TokenService
from repositories.sql_repositories import UserRepository
from services.auth_service import AuthService
from services.chat_service import ChatService


class UserContext(TypedDict):
    user_id: str
    email: str
    display_name: str
    roles: list[str]


def get_container(request: Request) -> ApplicationContainer:
    container: ApplicationContainer = request.app.state.container
    return container


ContainerDep = Annotated[ApplicationContainer, Depends(get_container)]


def get_runtime_settings(container: ContainerDep) -> Settings:
    return container.settings


SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]


async def get_session(container: ContainerDep) -> AsyncIterator[AsyncSession]:
    async with container.database.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    settings: SettingsDep,
    authorization: Annotated[str | None, Header()] = None,
) -> UserContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthenticationError("Missing bearer token")
    payload = TokenService(settings).decode(authorization.split(" ", 1)[1], expected_type="access")
    user = await UserRepository(session).get(str(payload["sub"]))
    if user is None or not user.is_active:
        raise AuthenticationError("Account is unavailable")
    return UserContext(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        roles=[user.role],
    )


CurrentUser = Annotated[UserContext, Depends(get_current_user)]


def get_auth_service(session: SessionDep, settings: SettingsDep) -> AuthService:
    return AuthService(session, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_chat_service(
    session: SessionDep,
    container: ContainerDep,
) -> ChatService:
    return ChatService(
        session,
        container.agent,
        container.settings,
        container.memory,
        container.costs,
    )


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
