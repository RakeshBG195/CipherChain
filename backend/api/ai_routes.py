from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from backend.ai.predictor import ModelNotLoaded, get_predictor
from backend.api.common import get_message_for, log_event
from backend.auth.deps import get_current_user
from backend.database.base import iso, utcnow
from backend.database.db import get_db
from backend.models.models import SecurityEvent, User
from backend.schemas.schemas import AnalyzeIn

router = APIRouter(prefix="/api/ai")


def _predictor():
    try:
        return get_predictor()
    except ModelNotLoaded as e:
        raise HTTPException(503, str(e))


@router.post("/analyze")
async def analyze(body: AnalyzeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The plaintext is analysed in memory and DISCARDED. Only category/score/confidence are stored."""
    pred = _predictor()
    result = await run_in_threadpool(pred.predict, body.text)
    if body.message_id is not None:
        m = get_message_for(db, body.message_id, user)
        ev = db.query(SecurityEvent).filter_by(event_type="THREAT_SCAN", message_id=m.id).first()
        if ev is None:
            ev = log_event(db, user.id, "THREAT_SCAN", message_id=m.id)
        ev.category, ev.risk_score, ev.confidence, ev.created_at = result["category"], result["risk_score"], result["confidence"], utcnow()
        ev.detail = result["explanation"]
    else:
        log_event(db, user.id, "MANUAL_SCAN", category=result["category"], risk=result["risk_score"],
                  conf=result["confidence"], detail="manual scan from AI Threat Detection page")
    db.commit()
    return result


@router.get("/status")
def status(user: User = Depends(get_current_user)):
    try:
        p = get_predictor()
        return {"loaded": True, "classes": p.classes, "synthetic_data": (p.metrics or {}).get("synthetic_data"),
                "dataset": (p.metrics or {}).get("dataset"), "n_features": (p.metrics or {}).get("n_features")}
    except ModelNotLoaded as e:
        return {"loaded": False, "error": str(e)}


@router.get("/metrics")
def metrics(user: User = Depends(get_current_user)):
    p = _predictor()
    if not p.metrics:
        raise HTTPException(404, "metrics.json missing - retrain with scripts/train_model.py")
    return p.metrics


@router.get("/threats")
def recent_threats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (db.query(SecurityEvent).filter(SecurityEvent.user_id == user.id, SecurityEvent.category.isnot(None))
            .order_by(SecurityEvent.created_at.desc()).limit(25).all())
    return [{"id": r.id, "type": r.event_type, "category": r.category, "risk_score": r.risk_score,
             "confidence": r.confidence, "message_id": r.message_id, "created_at": iso(r.created_at)} for r in rows]
