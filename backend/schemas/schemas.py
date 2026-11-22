from typing import Optional
from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    username: str = Field(pattern=r"^[A-Za-z0-9_]{3,32}$")
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=120)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=64)
    public_key: str


class LoginIn(BaseModel):
    username: str
    password: str


class ProfileIn(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    bio: Optional[str] = Field(default=None, max_length=280)


class PublicKeyIn(BaseModel):
    public_key: str


class ConversationIn(BaseModel):
    peer_id: int


class SendIn(BaseModel):
    nonce: str = Field(min_length=16, max_length=24)        # 12 bytes base64 = 16 chars
    ciphertext: str = Field(min_length=24, max_length=40000)


class AnalyzeIn(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    message_id: Optional[int] = None
