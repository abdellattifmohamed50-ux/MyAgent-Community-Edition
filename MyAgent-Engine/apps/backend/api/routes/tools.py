from __future__ import annotations

from fastapi import APIRouter

from apps.backend.api.dependencies import ContainerDep, CurrentUser
from core.security.rbac import Role, require_role
from models.schemas import ToolExecuteRequest, ToolExecuteResponse, ToolInfo

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("", response_model=list[ToolInfo])
async def list_tools(user: CurrentUser, container: ContainerDep) -> list[ToolInfo]:
    require_role(user["roles"], Role.USER)
    return [
        ToolInfo(name=item.name, description=item.description) for item in container.tools.all()
    ]


@router.post("/{tool_name}/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    tool_name: str,
    payload: ToolExecuteRequest,
    user: CurrentUser,
    container: ContainerDep,
) -> ToolExecuteResponse:
    require_role(user["roles"], Role.USER)
    result = await container.tools.get(tool_name).execute(**payload.arguments)
    return ToolExecuteResponse(
        ok=result.ok,
        output=result.output,
        metadata=result.metadata,
    )
