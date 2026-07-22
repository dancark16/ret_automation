from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.progress import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/progress")
async def websocket_progress(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # mantener conexión viva (ping del cliente)
    except WebSocketDisconnect:
        manager.disconnect(ws)
