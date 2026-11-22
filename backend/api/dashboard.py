from collections import defaultdict
from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.ai.predictor import ModelNotLoaded, get_predictor
from backend.auth.deps import get_current_user
from backend.database.base import iso, utcnow
from backend.database.db import get_db
from backend.models.models import BlockchainRecord, Conversation, EncryptedMessage, SecurityEvent, User

router = APIRouter(prefix="/api/dashboard")
DAYS = 14


@router.get("/summary")
def summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv_ids = [c.id for c in db.query(Conversation.id).filter(or_(Conversation.user_a_id == user.id, Conversation.user_b_id == user.id))]
    msgs = db.query(EncryptedMessage).filter(EncryptedMessage.conversation_id.in_(conv_ids)) if conv_ids else None
    total = msgs.count() if msgs is not None else 0
    ids = [i for (i,) in msgs.with_entities(EncryptedMessage.id)] if msgs is not None else []
    encrypted = msgs.filter(EncryptedMessage.ciphertext != "", EncryptedMessage.nonce != "").count() if msgs is not None else 0
    rec = db.query(BlockchainRecord).filter(BlockchainRecord.message_id.in_(ids)) if ids else None
    recorded = rec.filter_by(status="RECORDED").count() if rec is not None else 0
    verified = rec.filter_by(last_status="VERIFIED").count() if rec is not None else 0
    tampered = rec.filter_by(last_status="TAMPERED").count() if rec is not None else 0

    scans = (db.query(SecurityEvent).filter(SecurityEvent.event_type == "THREAT_SCAN", SecurityEvent.message_id.in_(ids)).all() if ids else [])
    dist = {"SAFE": 0, "SPAM": 0, "PHISHING": 0}
    for s in scans:
        dist[s.category] = dist.get(s.category, 0) + 1

    today = utcnow().date()
    days = [today - timedelta(days=i) for i in range(DAYS - 1, -1, -1)]
    since = utcnow() - timedelta(days=DAYS)
    daily = defaultdict(int)
    if msgs is not None:
        for (ts,) in msgs.filter(EncryptedMessage.created_at >= since).with_entities(EncryptedMessage.created_at):
            daily[ts.date()] += 1
    hist = defaultdict(lambda: {"SAFE": 0, "SPAM": 0, "PHISHING": 0})
    for e in db.query(SecurityEvent).filter(SecurityEvent.user_id == user.id, SecurityEvent.category.isnot(None),
                                            SecurityEvent.created_at >= since):
        hist[e.created_at.date()][e.category] += 1

    metrics = None
    try:
        metrics = get_predictor().metrics
    except ModelNotLoaded:
        pass
    events = db.query(SecurityEvent).filter_by(user_id=user.id).order_by(SecurityEvent.created_at.desc()).limit(15).all()
    return {
        "totals": {"total_messages": total, "encrypted_messages": encrypted, "blockchain_recorded": recorded,
                   "blockchain_verified": verified, "tampered": tampered,
                   "spam_detected": dist["SPAM"], "phishing_detected": dist["PHISHING"], "scanned_messages": len(scans)},
        "category_distribution": dist,
        "daily_activity": [{"date": d.isoformat(), "messages": daily.get(d, 0)} for d in days],
        "threat_history": [{"date": d.isoformat(), **hist.get(d, {"SAFE": 0, "SPAM": 0, "PHISHING": 0})} for d in days],
        "model_metrics": metrics,
        "recent_events": [{"id": e.id, "type": e.event_type, "category": e.category, "risk_score": e.risk_score,
                           "detail": e.detail, "message_id": e.message_id, "created_at": iso(e.created_at)} for e in events],
    }
