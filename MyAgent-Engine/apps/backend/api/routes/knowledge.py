from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, File, Form, Query, Response, UploadFile, status

from apps.backend.api.dependencies import CurrentUser, SessionDep
from core.documents.parsers import DocumentParser
from core.exceptions.base import AuthorizationError, ValidationError
from models.entities import KnowledgeDocument
from models.schemas import KnowledgeCreate, KnowledgeResponse
from repositories.sql_repositories import KnowledgeRepository, ProjectRepository

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("", response_model=list[KnowledgeResponse])
async def list_knowledge(
    user: CurrentUser,
    session: SessionDep,
    project_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[KnowledgeResponse]:
    items = await KnowledgeRepository(session).list_for_user(
        user["user_id"], project_id, limit=limit, offset=offset
    )
    return [KnowledgeResponse.model_validate(item) for item in items]


@router.post("", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge(
    payload: KnowledgeCreate,
    user: CurrentUser,
    session: SessionDep,
) -> KnowledgeResponse:
    await _validate_project(payload.project_id, user["user_id"], session)
    entity = KnowledgeDocument(
        id=f"doc_{uuid4().hex}",
        user_id=user["user_id"],
        **payload.model_dump(),
    )
    await KnowledgeRepository(session).add(entity)
    await session.commit()
    await session.refresh(entity)
    return KnowledgeResponse.model_validate(entity)


@router.post("/upload", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def upload_knowledge(
    user: CurrentUser,
    session: SessionDep,
    file: UploadFile = File(),
    project_id: str | None = Form(default=None),
) -> KnowledgeResponse:
    await _validate_project(project_id, user["user_id"], session)
    raw = await file.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValidationError("Knowledge file is larger than 2 MB")
    parsed = DocumentParser().parse_upload(file.filename, file.content_type, raw)
    entity = KnowledgeDocument(
        id=f"doc_{uuid4().hex}",
        user_id=user["user_id"],
        project_id=project_id,
        title=parsed.title,
        content=parsed.content,
        source_type=parsed.source_type,
    )
    await KnowledgeRepository(session).add(entity)
    await session.commit()
    await session.refresh(entity)
    return KnowledgeResponse.model_validate(entity)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_knowledge(
    document_id: str,
    user: CurrentUser,
    session: SessionDep,
) -> Response:
    repository = KnowledgeRepository(session)
    entity = await repository.get_for_user(document_id, user["user_id"])
    if entity is None:
        raise AuthorizationError("Knowledge document was not found")
    await repository.delete(entity)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _validate_project(project_id: str | None, user_id: str, session: SessionDep) -> None:
    if project_id is None:
        return
    if await ProjectRepository(session).get_for_user(project_id, user_id) is None:
        raise AuthorizationError("Project was not found")
