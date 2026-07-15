from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from apps.backend.api.dependencies import AuthServiceDep, CurrentUser, SessionDep
from models.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from repositories.sql_repositories import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    service: AuthServiceDep,
) -> TokenResponse:
    return await service.register(
        str(payload.email),
        payload.password,
        payload.display_name,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    service: AuthServiceDep,
) -> TokenResponse:
    return await service.login(
        str(payload.email),
        payload.password,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, service: AuthServiceDep) -> TokenResponse:
    return await service.refresh(payload.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def logout(payload: LogoutRequest, service: AuthServiceDep) -> Response:
    await service.logout(payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser, session: SessionDep) -> UserResponse:
    entity = await UserRepository(session).get(user["user_id"])
    if entity is None:  # Defensive; authentication dependency already checked this.
        raise RuntimeError("Authenticated user disappeared")
    return UserResponse.model_validate(entity)
