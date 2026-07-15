from __future__ import annotations

import asyncio

from fastapi import APIRouter

from apps.backend.api.dependencies import ContainerDep, CurrentUser
from models.schemas import ProviderInfo

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=list[ProviderInfo])
async def providers(user: CurrentUser, container: ContainerDep) -> list[ProviderInfo]:
    del user
    items = container.providers.all()
    health = await asyncio.gather(*(item.health() for item in items), return_exceptions=True)
    return [
        ProviderInfo(
            name=item.name,
            model=item.model,
            configured=item.configured,
            healthy=result is True,
            is_default=item.name == container.settings.default_provider,
        )
        for item, result in zip(items, health, strict=True)
    ]
