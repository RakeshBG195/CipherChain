import base64

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from backend.api.common import get_conversation_for, log_event, message_out, peer_of
from backend.api.ws import manager
from backend.auth.deps import get_current_user
from backend.blockchain.service import LedgerUnavailable, chain_key, get_ledger
from backend.crypto.e2ee import payload_hash
from backend.database.base import utcnow
from backend.database.db import get_db
from backend.models.models import BlockchainRecord, DeliveryStatus, EncryptedMessage, SecurityEvent, User
from backend.schemas.schemas import SendIn

router = APIRouter(prefix="/api")


def scans_for(db, ids):
    if not ids:
        return {}
    rows = db.query(SecurityEvent).filter(SecurityEvent.event_type == "THREAT_SCAN", SecurityEvent.message_id.in_(ids)).all()
    return {r.message_id: {"category": r.category, "risk_score": r.risk_score, "confidence": r.confidence} for r in rows}


@router.post("/conversations/{conv_id}/messages", status_code=201)
async def send_message(conv_id: int, body: SendIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = get_conversation_for(db, conv_id, user)
    peer = peer_of(conv, user)
    try:
        if len(base64.b64decode(body.nonce, validate=True)) != 12:
            raise ValueError
        if len(base64.b64decode(body.ciphertext, validate=True)) < 17:   # at least 1 byte + 16-byte GCM tag
            raise ValueError
    except Exception:
        raise HTTPException(400, "nonce must be 12 bytes and ciphertext must be AES-GCM output, both base64")
    h = payload_hash(conv.id, user.id, body.nonce, body.ciphertext)
    m = EncryptedMessage(conversation_id=conv.id, sender_id=user.id, nonce=body.nonce, ciphertext=body.ciphertext,
                         payload_hash=h, created_at=utcnow())
    db.add(m); db.flush()
    online = manager.is_online(peer.id)
    db.add(DeliveryStatus(message_id=m.id, status="delivered" if online else "sent", sent_at=utcnow(),
                          delivered_at=utcnow() if online else None))
    rec = BlockchainRecord(message_id=m.id, payload_hash=h, status="PENDING")
    db.add(rec)
    try:  # record the hash of the ENCRYPTED payload on the real blockchain
        info = await run_in_threadpool(get_ledger().record, chain_key(m.uid), h)
        rec.status, rec.tx_hash, rec.block_number, rec.chain_timestamp = "RECORDED", info["tx_hash"], info["block_number"], info["timestamp"]
    except LedgerUnavailable as e:
        rec.status, rec.error = "FAILED", str(e)[:500]
        log_event(db, user.id, "CHAIN_RECORD_FAILED", message_id=m.id, detail=str(e)[:300])
    db.commit(); db.refresh(m)
    out = message_out(m)
    await manager.send(peer.id, {"type": "message.new", "message": out})
    return out


@router.get("/conversations/{conv_id}/messages")
async def list_messages(conv_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_conversation_for(db, conv_id, user)
    msgs = db.query(EncryptedMessage).filter_by(conversation_id=conv_id).order_by(EncryptedMessage.id).all()
    changed = []
    for m in msgs:  # opening the conversation counts as delivery of the peer's messages
        if m.sender_id != user.id and m.delivery and m.delivery.status == "sent":
            m.delivery.status, m.delivery.delivered_at = "delivered", utcnow()
            changed.append(m)
    db.commit()
    for m in changed:
        await manager.send(m.sender_id, {"type": "message.status", "message_id": m.id, "conversation_id": conv_id, "status": "delivered"})
    scans = scans_for(db, [m.id for m in msgs])
    return [message_out(m, scans.get(m.id)) for m in msgs]


@router.post("/conversations/{conv_id}/read")
async def mark_read(conv_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = get_conversation_for(db, conv_id, user)
    rows = (db.query(DeliveryStatus).join(EncryptedMessage, EncryptedMessage.id == DeliveryStatus.message_id)
            .filter(EncryptedMessage.conversation_id == conv_id, EncryptedMessage.sender_id != user.id,
                    DeliveryStatus.status != "read").all())
    ids = []
    for d in rows:
        d.status, d.read_at = "read", utcnow()
        d.delivered_at = d.delivered_at or d.read_at
        ids.append(d.message_id)
    db.commit()
    if ids:
        await manager.send(peer_of(conv, user).id, {"type": "message.read", "conversation_id": conv_id, "message_ids": ids})
    return {"marked_read": len(ids)}
