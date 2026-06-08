"""WebSocket chat transport (same events as SSE /chat/stream)."""

from __future__ import annotations

import json

from fastapi import HTTPException, WebSocket, WebSocketDisconnect

from app.auth import AuthContext, resolve_customer_id, resolve_tenant_id
from app.service import iter_chat_events


async def handle_chat_websocket(
    websocket: WebSocket,
    *,
    auth: AuthContext | None,
) -> None:
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"event": "error", "data": {"detail": "Invalid JSON"}}
                )
                continue

            session_id = payload.get("session_id")
            message = payload.get("message")
            if not session_id or not message:
                await websocket.send_json(
                    {
                        "event": "error",
                        "data": {"detail": "session_id and message are required"},
                    }
                )
                continue

            try:
                customer_id = resolve_customer_id(auth, payload.get("customer_id"))
                tenant_id = resolve_tenant_id(auth, payload.get("tenant_id"))
            except HTTPException as exc:
                await websocket.send_json(
                    {"event": "error", "data": {"detail": exc.detail}}
                )
                continue

            async for event, data in iter_chat_events(
                session_id=session_id,
                message=message,
                customer_id=customer_id,
                tenant_id=tenant_id,
            ):
                await websocket.send_json({"event": event, "data": data})
    except WebSocketDisconnect:
        return
