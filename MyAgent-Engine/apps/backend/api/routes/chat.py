from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from apps.backend.api.dependencies import ChatServiceDep, CurrentUser
from models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    user: CurrentUser,
    service: ChatServiceDep,
) -> ChatResponse:
    return await service.chat(user["user_id"], payload)


@router.post("/stream")
async def stream_chat(
    payload: ChatRequest,
    user: CurrentUser,
    service: ChatServiceDep,
) -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        async for event in service.stream(user["user_id"], payload):
            yield "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
