from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from core.container import ApplicationContainer
from core.logging.logger import get_logger
from core.security.jwt import TokenService
from models.schemas import ChatRequest
from repositories.sql_repositories import UserRepository
from services.chat_service import ChatService

router = APIRouter(tags=["websocket"])
logger = get_logger(__name__)

_BROWSER_PROTOCOL = "myagent-v1"
_AUTH_PROTOCOL_PREFIX = "myagent.jwt."


def _extract_access_token(websocket: WebSocket) -> tuple[str | None, str | None]:
    """Extract a bearer token without placing it in the request URL.

    Native clients should send ``Authorization: Bearer <token>``. Browser
    clients can request ``myagent-v1`` and ``myagent.jwt.<token>`` subprotocols;
    only the non-secret ``myagent-v1`` protocol is echoed in the handshake.
    """
    authorization = websocket.headers.get("authorization", "")
    scheme, separator, credential = authorization.partition(" ")
    if separator and scheme.lower() == "bearer" and credential.strip():
        return credential.strip(), None

    requested_protocols = [
        value.strip()
        for value in websocket.headers.get("sec-websocket-protocol", "").split(",")
        if value.strip()
    ]
    for protocol in requested_protocols:
        if protocol.startswith(_AUTH_PROTOCOL_PREFIX):
            token = protocol.removeprefix(_AUTH_PROTOCOL_PREFIX).strip()
            selected_protocol = (
                _BROWSER_PROTOCOL if _BROWSER_PROTOCOL in requested_protocols else None
            )
            return (token or None), selected_protocol
    return None, None


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    container: ApplicationContainer = websocket.app.state.container
    token, selected_protocol = _extract_access_token(websocket)
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return
    try:
        payload = TokenService(container.settings).decode(token, expected_type="access")
    except Exception:  # noqa: BLE001 - do not leak token validation details
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    async with container.database.session_factory() as session:
        user = await UserRepository(session).get(str(payload["sub"]))
        if user is None or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid user")
            return
        service = ChatService(
            session,
            container.agent,
            container.settings,
            container.memory,
            container.costs,
        )
        await websocket.accept(subprotocol=selected_protocol)
        await websocket.send_json({"type": "ready", "user_id": user.id})
        try:
            while True:
                request = ChatRequest.model_validate(await websocket.receive_json())
                async for event in service.stream(user.id, request):
                    await websocket.send_json(event)
        except WebSocketDisconnect:
            return
        except Exception:  # noqa: BLE001 - log internally, return bounded error
            logger.exception("WebSocket chat request failed")
            await websocket.send_json({"type": "error", "message": "Chat request failed"})
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
