from typing import Dict, Set

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import or_

from backend.auth.security import decode_token
from backend.database.base import iso, utcnow
from backend.database.db import SessionLocal
from backend.models.models import Conversation, DeliveryStatus, EncryptedMessage, User

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active: Dict[int, Set[WebSocket]] = {}

    def is_online(self, uid: int) -> bool:
        return bool(self.active.get(uid))

    async def send(self, uid: int, event: dict):
        for ws in list(self.active.get(uid, ())):
            try:
                await ws.send_json(event)
            except Exception:
                self.active[uid].discard(ws)


manager = ConnectionManager()


def _peer_ids(db, uid):
    rows = db.query(Conversation).filter(or_(Conversation.user_a_id == uid, Conversation.user_b_id == uid)).all()
    return [c.user_b_id if c.user_a_id == uid else c.user_a_id for c in rows]


async def _broadcast_presence(db, user):
    for pid in _peer_ids(db, user.id):
        await manager.send(pid, {"type": "presence", "user_id": user.id, "is_online": bool(user.is_online), "last_seen": iso(user.last_seen)})


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket, token: str = Query(...)):
    try:
        uid = int(decode_token(token)["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        await ws.close(code=4401)
        return
    db = SessionLocal()
    try:
        user = db.get(User, uid)
        if user is None:
            await ws.close(code=4401)
            return
        await ws.accept()
        manager.active.setdefault(uid, set()).add(ws)
        user.is_online, user.last_seen = True, utcnow()
        # messages that arrived while offline are now delivered
        pending = (db.query(DeliveryStatus).join(EncryptedMessage, EncryptedMessage.id == DeliveryStatus.message_id)
                   .join(Conversation, Conversation.id == EncryptedMessage.conversation_id)
                   .filter(DeliveryStatus.status == "sent", EncryptedMessage.sender_id != uid,
                           or_(Conversation.user_a_id == uid, Conversation.user_b_id == uid)).all())
        notify = []
        for d in pending:
            d.status, d.delivered_at = "delivered", utcnow()
            notify.append((d.message.sender_id, d.message_id, d.message.conversation_id))
        db.commit()
        for sender_id, mid, cid in notify:
            await manager.send(sender_id, {"type": "message.status", "message_id": mid, "conversation_id": cid, "status": "delivered"})
        await _broadcast_presence(db, user)
        try:
            while True:
                if (await ws.receive_text()) == "ping":
                    await ws.send_json({"type": "pong"})
        except WebSocketDisconnect:
            pass
    finally:
        s = manager.active.get(uid)
        if s is not None:
            s.discard(ws)
        user = db.get(User, uid)
        if user is not None and not manager.is_online(uid):
            user.is_online, user.last_seen = False, utcnow()
            db.commit()
            await _broadcast_presence(db, user)
        db.close()
