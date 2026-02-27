import logging
import os
import time
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from repositories.db import init_db
from routers import (
    create_auth_router,
    create_chat_router,
    create_ingest_router,
    create_session_router,
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


app.include_router(create_auth_router(auth_service=auth_service, get_current_user=get_current_user))
app.include_router(
    create_session_router(
        session_service=session_service,
        get_current_user=get_current_user,
    )
)
app.include_router(
    create_ingest_router(
        rag_service=rag_service,
        ingest_job_service=ingest_job_service,
    )
)
app.include_router(
    create_chat_router(
        rag_service=rag_service,
        session_service=session_service,
        get_current_user_optional=get_current_user_optional,
    )
)
