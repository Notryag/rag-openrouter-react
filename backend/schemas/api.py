from typing import List, Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class UserResponse(BaseModel):
    id: int
    username: str


class SessionCreateRequest(BaseModel):
    title: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str


class SessionMessage(BaseModel):
    question: str
    answer: str
    created_at: str


class IngestRequest(BaseModel):
    reset: bool = True


class IngestJobResponse(BaseModel):
    id: int
    status: str
    reset: bool
    files: int
    chunks: int
    failed: List[str]
    error: Optional[str] = None
    created_at: str
    updated_at: str


class ChatRequest(BaseModel):
    question: str
    k: int = 4
    session_id: Optional[int] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    session_id: Optional[int] = None
