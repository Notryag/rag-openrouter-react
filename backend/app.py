import os
import shutil
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain

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


_embeddings = None
_llm = None
_vectorstore = None


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


class IngestRequest(BaseModel):
    reset: bool = True


class ChatRequest(BaseModel):
    question: str
    k: int = 4


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]


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
def chat(payload: ChatRequest):
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
    return ChatResponse(
        answer=result.get("answer", ""),
        sources=build_sources(docs),
    )
