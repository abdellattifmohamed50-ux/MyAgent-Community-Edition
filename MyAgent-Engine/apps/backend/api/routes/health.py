from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Response, status

from apps.backend.api.dependencies import ContainerDep
from models.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse)
async def live(container: ContainerDep) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="myagent-engine",
        version=container.settings.app_version,
        environment=container.settings.environment,
        checks={"process": True},
    )


@router.get("", response_model=HealthResponse)
@router.get("/ready", response_model=HealthResponse)
async def ready(response: Response, container: ContainerDep) -> HealthResponse:
    checks: dict[str, bool] = {}
    try:
        checks["database"] = await container.database.health()
    except Exception:  # noqa: BLE001 - readiness must report rather than crash
        checks["database"] = False
    health_status: Literal["ok", "degraded", "error"] = "ok" if all(checks.values()) else "degraded"
    if health_status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status=health_status,
        service="myagent-engine",
        version=container.settings.app_version,
        environment=container.settings.environment,
        checks=checks,
    )
