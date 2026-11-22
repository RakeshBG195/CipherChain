from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.api.common import peer_of, user_out
from backend.auth.deps import get_current_user
from backend.database.base import iso
from backend.database.db import get_db
from backend.models.models import Conversation, DeliveryStatus, EncryptedMessage, User
from backend.schemas.schemas import ConversationIn

router = APIRouter(prefix="/api")


def conv_out(db, c: Conversation, user: User) -> dict:
    last = (db.query(EncryptedMessage).filter_by(conversation_id=c.id).order_by(EncryptedMessage.id.desc()).first())
    unread = (db.query(func.count(DeliveryStatus.id)).join(EncryptedMessage, EncryptedMessage.id == DeliveryStatus.message_id)
              .filter(EncryptedMessage.conversation_id == c.id, EncryptedMessage.sender_id != user.id,
                      DeliveryStatus.status != "read").scalar())
    return {"id": c.id, "peer": user_out(peer_of(c, user)), "created_at": iso(c.created_at), "unread": int(unread or 0),
            "last_message_at": iso(last.created_at) if last else None}


@router.post("/conversations")
def open_conversation(body: ConversationIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.peer_id == user.id:
        raise HTTPException(400, "Cannot start a conversation with yourself")
    peer = db.get(User, body.peer_id)
    if peer is None:
        raise HTTPException(404, "User not found")
    a, b = sorted((user.id, peer.id))
    c = db.query(Conversation).filter_by(user_a_id=a, user_b_id=b).first()
    if c is None:
        c = Conversation(user_a_id=a, user_b_id=b)
        db.add(c); db.commit(); db.refresh(c)
    return conv_out(db, c, user)


@router.get("/conversations")
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cs = db.query(Conversation).filter(or_(Conversation.user_a_id == user.id, Conversation.user_b_id == user.id)).all()
    out = [conv_out(db, c, user) for c in cs]
    out.sort(key=lambda x: x["last_message_at"] or x["created_at"], reverse=True)
    return out
