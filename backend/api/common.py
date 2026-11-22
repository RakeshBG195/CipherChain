from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.database.base import iso, utcnow
from backend.models.models import Conversation, EncryptedMessage, SecurityEvent, User


def user_out(u: User, with_key: bool = True) -> dict:
    d = {"id": u.id, "username": u.username, "display_name": u.display_name, "bio": u.bio or "",
         "is_online": bool(u.is_online), "last_seen": iso(u.last_seen), "created_at": iso(u.created_at)}
    if with_key:
        d["public_key"] = u.public_key
    return d


def log_event(db: Session, user_id, event_type, message_id=None, category=None, risk=None, conf=None, detail=""):
    ev = SecurityEvent(user_id=user_id, message_id=message_id, event_type=event_type, category=category,
                       risk_score=risk, confidence=conf, detail=detail, created_at=utcnow())
    db.add(ev)
    return ev


def get_conversation_for(db: Session, conv_id: int, user: User) -> Conversation:
    c = db.get(Conversation, conv_id)
    if c is None or user.id not in (c.user_a_id, c.user_b_id):
        raise HTTPException(404, "Conversation not found")
    return c


def peer_of(c: Conversation, user: User) -> User:
    return c.user_b if c.user_a_id == user.id else c.user_a


def get_message_for(db: Session, message_id: int, user: User) -> EncryptedMessage:
    m = db.get(EncryptedMessage, message_id)
    if m is None:
        raise HTTPException(404, "Message not found")
    get_conversation_for(db, m.conversation_id, user)
    return m


def message_out(m: EncryptedMessage, scan=None) -> dict:
    d, b = m.delivery, m.blockchain
    return {
        "id": m.id, "uid": m.uid, "conversation_id": m.conversation_id, "sender_id": m.sender_id,
        "nonce": m.nonce, "ciphertext": m.ciphertext, "payload_hash": m.payload_hash, "created_at": iso(m.created_at),
        "status": d.status if d else "sent", "delivered_at": iso(d.delivered_at) if d else None, "read_at": iso(d.read_at) if d else None,
        "blockchain": {"status": b.status, "tx_hash": b.tx_hash, "block_number": b.block_number,
                       "last_status": b.last_status} if b else None,
        "scan": scan,
    }
