import os
import shutil
import sqlite3
import hashlib
import secrets
import time
import uuid
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"
AUTH_DB_PATH = APP_DIR / "app.db"

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


class ChatRequest(BaseModel):
    question: str
    k: int = 4
    session_id: Optional[int] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    session_id: Optional[int] = None


_embeddings = None
_llm = None
_vectorstore = None


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


def _default_headers():
    headers = {}
    if APP_NAME:
        headers["X-Title"] = APP_NAME
    if APP_URL:
        headers["HTTP-Referer"] = APP_URL
    return headers or None


def _require_api_key():
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _require_api_key()
        _embeddings = OpenAIEmbeddings(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            model=OPENROUTER_EMBEDDING_MODEL,
            default_headers=_default_headers(),
        )
    return _embeddings


def get_llm():
    global _llm
    if _llm is None:
        _require_api_key()
        _llm = ChatOpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            model=OPENROUTER_MODEL,
            temperature=0.2,
            default_headers=_default_headers(),
        )
    return _llm


def has_index():
    return CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir())


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        if not has_index():
            raise RuntimeError("Vector index not found. Run ingest first.")
        _vectorstore = Chroma(
            collection_name="rag",
            persist_directory=str(CHROMA_DIR),
            embedding_function=get_embeddings(),
        )
    return _vectorstore


def get_db():
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
            )
            """
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 390000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, expected = stored_hash.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 390000)
    return secrets.compare_digest(digest.hex(), expected)


def create_access_token(user_id: int, username: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": expires,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    if credentials is None:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
        username = payload.get("username")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, username FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="User not found")
    return {"id": row["id"], "username": row["username"]}


def get_current_user(
    user=Depends(get_current_user_optional),
):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def create_session_for_user(user_id: int, title: str) -> int:
    timestamp = now_iso()
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO chat_sessions (user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (user_id, title[:120], timestamp, timestamp),
        )
        return int(cur.lastrowid)


def ensure_session_owner(session_id: int, user_id: int):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")


def save_message(session_id: int, question: str, answer: str):
    timestamp = now_iso()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO chat_messages (session_id, question, answer, created_at) VALUES (?, ?, ?, ?)",
            (session_id, question, answer, timestamp),
        )
        conn.execute(
            "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
            (timestamp, session_id),
        )


def collect_files():
    if not DATA_DIR.exists():
        return []
    exts = {".txt", ".md", ".pdf"}
    return [p for p in DATA_DIR.rglob("*") if p.is_file() and p.suffix.lower() in exts]


def load_documents(files: List[Path]):
    docs = []
    failed = []
    for path in files:
        try:
            if path.suffix.lower() == ".pdf":
                loader = PyPDFLoader(str(path))
            else:
                loader = TextLoader(str(path), encoding="utf-8")
            docs.extend(loader.load())
        except Exception as exc:
            failed.append(f"{path}: {exc}")
    return docs, failed


def build_sources(docs):
    sources = []
    for doc in docs:
        src = doc.metadata.get("source")
        page = doc.metadata.get("page")
        entry = {}
        if src:
            entry["source"] = str(src)
        if page is not None:
            entry["page"] = page
        if entry:
            sources.append(entry)
    return sources


def make_session_title(question: str) -> str:
    cleaned = " ".join(question.split()).strip()
    if not cleaned:
        return "New chat"
    return cleaned[:60]


@app.on_event("startup")
def on_startup():
    init_db()


@app.post("/auth/register", response_model=UserResponse)
def register(payload: RegisterRequest):
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing is not None:
            raise HTTPException(status_code=409, detail="Username already exists")
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, hash_password(payload.password), now_iso()),
        )
    return UserResponse(id=int(cur.lastrowid), username=username)


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    username = payload.username.strip()
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row is None or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(int(row["id"]), row["username"])
    return TokenResponse(access_token=token, username=row["username"])


@app.get("/auth/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return UserResponse(id=user["id"], username=user["username"])


@app.get("/sessions", response_model=List[SessionResponse])
def list_sessions(user=Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM chat_sessions
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user["id"],),
        ).fetchall()
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
    session_id = create_session_for_user(user["id"], title)
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    return SessionResponse(
        id=int(row["id"]),
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@app.get("/sessions/{session_id}/messages", response_model=List[SessionMessage])
def get_session_messages(session_id: int, user=Depends(get_current_user)):
    ensure_session_owner(session_id, user["id"])
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT question, answer, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()
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
    global _vectorstore
    files = collect_files()
    if not files:
        raise HTTPException(status_code=400, detail="No supported files in data/")
    if payload.reset and CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
    docs, failed = load_documents(files)
    if not docs:
        raise HTTPException(status_code=400, detail="No documents loaded.")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(docs)
    vectorstore = Chroma.from_documents(
        chunks,
        embedding=get_embeddings(),
        persist_directory=str(CHROMA_DIR),
        collection_name="rag",
    )
    _vectorstore = vectorstore
    return {
        "files": len(files),
        "chunks": len(chunks),
        "failed": failed,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, user=Depends(get_current_user_optional)):
    try:
        vectorstore = get_vectorstore()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    retriever = vectorstore.as_retriever(search_kwargs={"k": payload.k})
    system = (
        "You are a helpful assistant. Answer using only the provided context. "
        "If the answer is not in the context, say you don't know."
    )
    prompt = ChatPromptTemplate.from_messages(
        [("system", system), ("human", "Question: {input}\n\nContext:\n{context}")]
    )
    combine_docs_chain = create_stuff_documents_chain(get_llm(), prompt)
    retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)
    result = retrieval_chain.invoke({"input": payload.question})
    docs = result.get("context", [])
    answer = result.get("answer", "")

    session_id = payload.session_id
    if user is not None:
        if session_id is None:
            session_id = create_session_for_user(user["id"], make_session_title(payload.question))
        else:
            ensure_session_owner(session_id, user["id"])
        save_message(session_id, payload.question, answer)

    return ChatResponse(
        answer=answer,
        sources=build_sources(docs),
        session_id=session_id,
    )
