from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Query, Response, status

from apps.backend.api.dependencies import CurrentUser, SessionDep
from core.exceptions.base import AuthorizationError
from models.entities import Project
from models.schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from repositories.sql_repositories import ProjectRepository

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    user: CurrentUser,
    session: SessionDep,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ProjectResponse]:
    items = await ProjectRepository(session).list_for_user(
        user["user_id"], limit=limit, offset=offset
    )
    return [ProjectResponse.model_validate(item) for item in items]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    user: CurrentUser,
    session: SessionDep,
) -> ProjectResponse:
    entity = Project(
        id=f"prj_{uuid4().hex}",
        owner_id=user["user_id"],
        **payload.model_dump(),
    )
    await ProjectRepository(session).add(entity)
    await session.commit()
    await session.refresh(entity)
    return ProjectResponse.model_validate(entity)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user: CurrentUser,
    session: SessionDep,
) -> ProjectResponse:
    entity = await ProjectRepository(session).get_for_user(project_id, user["user_id"])
    if entity is None:
        raise AuthorizationError("Project was not found")
    return ProjectResponse.model_validate(entity)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    user: CurrentUser,
    session: SessionDep,
) -> ProjectResponse:
    repository = ProjectRepository(session)
    entity = await repository.get_for_user(project_id, user["user_id"])
    if entity is None:
        raise AuthorizationError("Project was not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(entity, key, value)
    await session.commit()
    await session.refresh(entity)
    return ProjectResponse.model_validate(entity)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_project(
    project_id: str,
    user: CurrentUser,
    session: SessionDep,
) -> Response:
    repository = ProjectRepository(session)
    entity = await repository.get_for_user(project_id, user["user_id"])
    if entity is None:
        raise AuthorizationError("Project was not found")
    await repository.delete(entity)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
