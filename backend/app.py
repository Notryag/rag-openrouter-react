import logging
import os
import time
import uuid
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from repositories.db import init_db
from schemas.api import (
    ChatRequest,
    ChatResponse,
    IngestJobResponse,
    IngestRequest,
    LoginRequest,
    RegisterRequest,
    SessionCreateRequest,
    SessionMessage,
    SessionResponse,
    TokenResponse,
    UserResponse,
)
from services.auth_service import AuthService
from services.ingest_job_service import IngestJobService
from services.rag_service import RagService
from services.session_service import SessionService

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_EMBEDDING_MODEL = os.getenv(
    "OPENROUTER_EMBEDDING_MODEL",
    "openai/text-embedding-3-small",
)

APP_NAME = os.getenv("OPENROUTER_APP_NAME")
APP_URL = os.getenv("OPENROUTER_APP_URL")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

bearer_scheme = HTTPBearer(auto_error=False)
logger = logging.getLogger("rag_api")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


auth_service = AuthService(
    jwt_secret=JWT_SECRET,
    jwt_algorithm=JWT_ALGORITHM,
    access_token_expire_minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
)
session_service = SessionService()
rag_service = RagService(
    data_dir=DATA_DIR,
    chroma_dir=CHROMA_DIR,
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
    model=OPENROUTER_MODEL,
    embedding_model=OPENROUTER_EMBEDDING_MODEL,
    app_name=APP_NAME,
    app_url=APP_URL,
)
ingest_job_service = IngestJobService(rag_service=rag_service, logger=logger)


app = FastAPI(title="RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_trace_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.exception(
            "request_failed request_id=%s method=%s path=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            elapsed_ms,
        )
        raise

    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_completed request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    return auth_service.get_current_user_optional(credentials)


def get_current_user(
    user=Depends(get_current_user_optional),
):
    return auth_service.require_user(user)


@app.on_event("startup")
def on_startup():
    init_db()


@app.post("/auth/register", response_model=UserResponse)
def register(payload: RegisterRequest):
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    created = auth_service.register_user(username, payload.password)
    return UserResponse(id=created["id"], username=created["username"])


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    username = payload.username.strip()
    result = auth_service.login_user(username, payload.password)
    return TokenResponse(access_token=result["access_token"], username=result["username"])


@app.get("/auth/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return UserResponse(id=user["id"], username=user["username"])


@app.get("/sessions", response_model=List[SessionResponse])
def list_sessions(user=Depends(get_current_user)):
    rows = session_service.list_sessions(user["id"])
    return [
        SessionResponse(
            id=int(row["id"]),
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


@app.post("/sessions", response_model=SessionResponse)
def create_session(payload: SessionCreateRequest, user=Depends(get_current_user)):
    title = (payload.title or "New chat").strip() or "New chat"
    session_id = session_service.create_session_for_user(user["id"], title)
    row = session_service.get_session(session_id)
    return SessionResponse(
        id=int(row["id"]),
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@app.get("/sessions/{session_id}/messages", response_model=List[SessionMessage])
def get_session_messages(session_id: int, user=Depends(get_current_user)):
    session_service.ensure_session_owner(session_id, user["id"])
    rows = session_service.list_messages(session_id)
    return [
        SessionMessage(
            question=row["question"],
            answer=row["answer"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


@app.post("/ingest")
def ingest(payload: IngestRequest):
    try:
        return rag_service.run_ingest(payload.reset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/ingest/jobs", response_model=IngestJobResponse)
def create_ingest_job_endpoint(payload: IngestRequest):
    job_id = ingest_job_service.create_ingest_job(payload.reset)
    return ingest_job_service.get_ingest_job(job_id)


@app.get("/ingest/jobs", response_model=List[IngestJobResponse])
def list_ingest_jobs_endpoint(limit: int = 20):
    return ingest_job_service.list_ingest_jobs(limit)


@app.get("/ingest/jobs/{job_id}", response_model=IngestJobResponse)
def get_ingest_job_endpoint(job_id: int):
    return ingest_job_service.get_ingest_job(job_id)


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, user=Depends(get_current_user_optional)):
    try:
        answer, sources = rag_service.answer_question(payload.question, payload.k)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    session_id = payload.session_id
    if user is not None:
        if session_id is None:
            session_id = session_service.create_session_for_user(
                user["id"],
                session_service.make_session_title(payload.question),
            )
        else:
            session_service.ensure_session_owner(session_id, user["id"])
        session_service.save_message(session_id, payload.question, answer)

    return ChatResponse(
        answer=answer,
        sources=sources,
        session_id=session_id,
    )
