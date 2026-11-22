from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.api.common import log_event, user_out
from backend.auth.deps import get_current_user
from backend.auth.security import create_token, hash_password, verify_password
from backend.crypto.e2ee import validate_public_key
from backend.database.base import utcnow
from backend.database.db import get_db
from backend.models.models import User
from backend.schemas.schemas import LoginIn, ProfileIn, PublicKeyIn, RegisterIn

router = APIRouter(prefix="/api")
_DUMMY = hash_password("dummy-password-for-timing")


@router.post("/auth/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    try:
        validate_public_key(body.public_key)
    except ValueError as e:
        raise HTTPException(400, str(e))
    uname, email = body.username.lower(), body.email.lower()
    if db.query(User).filter(or_(func.lower(User.username) == uname, func.lower(User.email) == email)).first():
        raise HTTPException(409, "Username or email already registered")
    u = User(username=uname, email=email, password_hash=hash_password(body.password),
             display_name=body.display_name.strip(), public_key=body.public_key)
    db.add(u); db.flush()
    log_event(db, u.id, "REGISTER", detail="account created")
    db.commit()
    return {"token": create_token(u.id), "user": user_out(u)}


@router.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    ident = body.username.lower().strip()
    u = db.query(User).filter(or_(User.username == ident, User.email == ident)).first()
    ok = verify_password(body.password, u.password_hash if u else _DUMMY)
    if not u or not ok:
        raise HTTPException(401, "Invalid credentials")
    u.last_seen = utcnow()
    log_event(db, u.id, "LOGIN", detail="login")
    db.commit()
    return {"token": create_token(u.id), "user": user_out(u)}


@router.get("/users/me")
def me(user: User = Depends(get_current_user)):
    return user_out(user)


@router.put("/users/me")
def update_me(body: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.display_name is not None:
        user.display_name = body.display_name.strip()
    if body.bio is not None:
        user.bio = body.bio
    db.commit()
    return user_out(user)


@router.put("/users/me/public-key")
def rotate_key(body: PublicKeyIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        validate_public_key(body.public_key)
    except ValueError as e:
        raise HTTPException(400, str(e))
    user.public_key = body.public_key
    log_event(db, user.id, "KEY_ROTATED", detail="identity public key replaced")
    db.commit()
    return user_out(user)


@router.get("/users")
def search_users(q: str = "", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    qs = db.query(User).filter(User.id != user.id)
    if q.strip():
        like = f"%{q.strip().lower()}%"
        qs = qs.filter(or_(func.lower(User.username).like(like), func.lower(User.display_name).like(like)))
    return [user_out(u, with_key=False) for u in qs.order_by(User.username).limit(20).all()]
