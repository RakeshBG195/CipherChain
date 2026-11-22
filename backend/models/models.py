import uuid
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database.base import Base, utcnow


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(32), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(64), nullable=False)
    bio = Column(String(280), default="")
    public_key = Column(String(128), nullable=False)       # base64 P-256 public point; private key never leaves the browser
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("user_a_id", "user_b_id"),)
    id = Column(Integer, primary_key=True)
    user_a_id = Column(Integer, ForeignKey("users.id"), nullable=False)   # always the smaller id
    user_b_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)
    user_a = relationship("User", foreign_keys=[user_a_id])
    user_b = relationship("User", foreign_keys=[user_b_id])


class EncryptedMessage(Base):
    """Only ciphertext is stored. There is deliberately no plaintext column."""
    __tablename__ = "encrypted_messages"
    id = Column(Integer, primary_key=True)
    uid = Column(String(32), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)  # on-chain key = int(uid, 16)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nonce = Column(String(32), nullable=False)             # base64 96-bit AES-GCM nonce
    ciphertext = Column(Text, nullable=False)              # base64 AES-256-GCM ciphertext || tag
    payload_hash = Column(String(64), nullable=False)      # SHA-256 hex computed at send time
    created_at = Column(DateTime, default=utcnow, index=True)
    delivery = relationship("DeliveryStatus", uselist=False, backref="message")
    blockchain = relationship("BlockchainRecord", uselist=False, backref="message")


class DeliveryStatus(Base):
    __tablename__ = "delivery_status"
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("encrypted_messages.id"), unique=True, nullable=False)
    status = Column(String(12), default="sent")            # sent | delivered | read
    sent_at = Column(DateTime, default=utcnow)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)


class BlockchainRecord(Base):
    __tablename__ = "blockchain_records"
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("encrypted_messages.id"), unique=True, nullable=False)
    payload_hash = Column(String(64), nullable=False)
    status = Column(String(12), default="PENDING")         # RECORDED | FAILED
    tx_hash = Column(String(80))
    block_number = Column(Integer)
    chain_timestamp = Column(Integer)
    error = Column(Text)
    last_status = Column(String(14))                       # last verification result: VERIFIED | TAMPERED | ...
    last_verified_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow)


class SecurityEvent(Base):
    __tablename__ = "security_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    message_id = Column(Integer, ForeignKey("encrypted_messages.id"), index=True)
    event_type = Column(String(24), nullable=False)        # THREAT_SCAN | MANUAL_SCAN | TAMPER_DETECTED | LOGIN | REGISTER | KEY_ROTATED | CHAIN_RECORD_FAILED
    category = Column(String(12))                          # SAFE | SPAM | PHISHING (scans)
    risk_score = Column(Float)
    confidence = Column(Float)
    detail = Column(Text, default="")                      # never contains message plaintext
    created_at = Column(DateTime, default=utcnow, index=True)
