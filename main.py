# routes/websocket.py

from fastapi import APIRouter, WebSocket

router = APIRouter()

connected_users = {}


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str
):

    await websocket.accept()

    connected_users[user_id] = websocket

    try:

        while True:

            await websocket.receive_text()

    except Exception:

        if user_id in connected_users:
            del connected_users[user_id]


async def send_alert(user_id, message):

    websocket = connected_users.get(user_id)

    if websocket:

        await websocket.send_json({
            "type": "fraud_alert",
            "message": message
        })