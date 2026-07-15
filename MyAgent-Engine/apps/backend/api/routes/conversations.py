from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Query, Response, status

from apps.backend.api.dependencies import CurrentUser, SessionDep
from core.exceptions.base import AuthorizationError
from models.entities import Conversation
from models.schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
)
from repositories.sql_repositories import ConversationRepository, ProjectRepository

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    user: CurrentUser,
    session: SessionDep,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ConversationResponse]:
    items = await ConversationRepository(session).list_for_user(
        user["user_id"], limit=limit, offset=offset
    )
    return [ConversationResponse.model_validate(item) for item in items]


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    user: CurrentUser,
    session: SessionDep,
) -> ConversationResponse:
    if payload.project_id:
        project = await ProjectRepository(session).get_for_user(payload.project_id, user["user_id"])
        if project is None:
            raise AuthorizationError("Project was not found")
    entity = Conversation(
        id=f"conv_{uuid4().hex}",
        user_id=user["user_id"],
        project_id=payload.project_id,
        title=payload.title,
        provider=payload.provider,
    )
    await ConversationRepository(session).add(entity)
    await session.commit()
    await session.refresh(entity)
    return ConversationResponse.model_validate(entity)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user: CurrentUser,
    session: SessionDep,
) -> ConversationResponse:
    entity = await _owned_conversation(conversation_id, user["user_id"], session)
    return ConversationResponse.model_validate(entity)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    user: CurrentUser,
    session: SessionDep,
) -> ConversationResponse:
    entity = await _owned_conversation(conversation_id, user["user_id"], session)
    entity.title = payload.title
    await session.commit()
    await session.refresh(entity)
    return ConversationResponse.model_validate(entity)


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: str,
    user: CurrentUser,
    session: SessionDep,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[MessageResponse]:
    await _owned_conversation(conversation_id, user["user_id"], session)
    items = await ConversationRepository(session).list_messages(
        conversation_id, limit=limit, offset=offset
    )
    return [MessageResponse.model_validate(item) for item in items]


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_conversation(
    conversation_id: str,
    user: CurrentUser,
    session: SessionDep,
) -> Response:
    entity = await _owned_conversation(conversation_id, user["user_id"], session)
    await ConversationRepository(session).delete(entity)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _owned_conversation(
    conversation_id: str,
    user_id: str,
    session: SessionDep,
) -> Conversation:
    entity = await ConversationRepository(session).get_for_user(conversation_id, user_id)
    if entity is None:
        raise AuthorizationError("Conversation was not found")
    return entity
