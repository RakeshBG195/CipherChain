from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.api.common import get_message_for, log_event
from backend.auth.deps import get_current_user
from backend.blockchain.integrity import UNAVAILABLE, TAMPERED, evaluate_integrity
from backend.blockchain.service import LedgerUnavailable, chain_key, get_ledger
from backend.config import ALLOW_DEV_TAMPER
from backend.crypto.e2ee import b64d, b64e, payload_hash
from backend.database.base import iso, utcnow
from backend.database.db import get_db
from backend.models.models import BlockchainRecord, Conversation, EncryptedMessage, User

router = APIRouter(prefix="/api/blockchain")


@router.get("/status")
async def chain_status(user: User = Depends(get_current_user)):
    return await run_in_threadpool(get_ledger().status)


def _user_msg_ids(db, user):
    return (db.query(EncryptedMessage.id).join(Conversation, Conversation.id == EncryptedMessage.conversation_id)
            .filter(or_(Conversation.user_a_id == user.id, Conversation.user_b_id == user.id)))


@router.get("/records")
def records(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (db.query(BlockchainRecord, EncryptedMessage).join(EncryptedMessage, EncryptedMessage.id == BlockchainRecord.message_id)
            .filter(BlockchainRecord.message_id.in_(_user_msg_ids(db, user).subquery().select()))
            .order_by(BlockchainRecord.id.desc()).limit(100).all())
    return [{"message_id": r.message_id, "conversation_id": m.conversation_id, "payload_hash": r.payload_hash, "status": r.status,
             "tx_hash": r.tx_hash, "block_number": r.block_number, "chain_timestamp": r.chain_timestamp, "error": r.error,
             "last_status": r.last_status, "last_verified_at": iso(r.last_verified_at), "created_at": iso(r.created_at)} for r, m in rows]


@router.get("/verify/{message_id}")
async def verify(message_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Recompute SHA-256 of the stored encrypted payload and compare with the hash stored ON-CHAIN."""
    m = get_message_for(db, message_id, user)
    rec = m.blockchain
    recomputed = payload_hash(m.conversation_id, m.sender_id, m.nonce, m.ciphertext)
    out = {"message_id": m.id, "recomputed_hash": recomputed, "stored_hash": m.payload_hash,
           "tx_hash": rec.tx_hash if rec else None, "block_number": rec.block_number if rec else None,
           "onchain_hash": None, "chain_timestamp": None}
    try:
        onchain = await run_in_threadpool(get_ledger().get, chain_key(m.uid))
    except LedgerUnavailable as e:
        out.update(status=UNAVAILABLE, error=str(e))
        return out
    out["onchain_hash"] = onchain["hash"] if onchain else None
    out["chain_timestamp"] = onchain["timestamp"] if onchain else None
    out["status"] = evaluate_integrity(recomputed, out["onchain_hash"])
    if rec:
        if out["status"] == TAMPERED and rec.last_status != TAMPERED:
            log_event(db, user.id, "TAMPER_DETECTED", message_id=m.id, detail="stored ciphertext no longer matches on-chain hash")
        rec.last_status, rec.last_verified_at = out["status"], utcnow()
        db.commit()
    return out


@router.post("/retry")
async def retry_failed(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Record messages whose on-chain write failed earlier (e.g. node was offline). Uses the hash computed at send time."""
    recs = (db.query(BlockchainRecord).filter(BlockchainRecord.status != "RECORDED",
            BlockchainRecord.message_id.in_(_user_msg_ids(db, user).subquery().select())).limit(50).all())
    done = 0
    for r in recs:
        m = db.get(EncryptedMessage, r.message_id)
        try:
            info = await run_in_threadpool(get_ledger().record, chain_key(m.uid), r.payload_hash)
        except LedgerUnavailable as e:
            r.error = str(e)[:500]
            break
        r.status, r.tx_hash, r.block_number, r.chain_timestamp, r.error = "RECORDED", info["tx_hash"], info["block_number"], info["timestamp"], None
        done += 1
    db.commit()
    return {"recorded": done, "remaining": len(recs) - done}


@router.post("/dev/tamper/{message_id}")
def dev_tamper(message_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """DEMO ONLY (ALLOW_DEV_TAMPER=1): flips one bit of the stored ciphertext to demonstrate tamper detection."""
    if not ALLOW_DEV_TAMPER:
        raise HTTPException(403, "Disabled. Start the backend with ALLOW_DEV_TAMPER=1 to enable this demo endpoint.")
    m = get_message_for(db, message_id, user)
    raw = bytearray(b64d(m.ciphertext)); raw[0] ^= 0x01
    m.ciphertext = b64e(bytes(raw))
    db.commit()
    return {"tampered": True, "message_id": m.id}
