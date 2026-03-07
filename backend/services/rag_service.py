import logging
import shutil
import threading
import time
from pathlib import Path

from chromadb.config import Settings as ChromaSettings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from services.functional_agent_runner import FunctionalAgentRunner
from services.rerank_service import EmbeddingRerankService

logger = logging.getLogger("rag_api.rag_service")


class RagService:
    def __init__(
        self,
        data_dir: Path,
        chroma_dir: Path,
        api_key: str,
        base_url: str,
        model: str,
        embedding_model: str,
        ai_timeout_seconds: float = 20,
        ai_max_retries: int = 1,
        chroma_anonymized_telemetry: bool = False,
        app_name: str | None = None,
        app_url: str | None = None,
        rerank_enabled: bool = False,
        rerank_fetch_k: int = 8,
    ):
        self.data_dir = data_dir
        self.chroma_dir = chroma_dir
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.embedding_model = embedding_model
        self.ai_timeout_seconds = max(float(ai_timeout_seconds), 1.0)
        self.ai_max_retries = max(int(ai_max_retries), 0)
        self.chroma_anonymized_telemetry = bool(chroma_anonymized_telemetry)
        self.app_name = app_name
        self.app_url = app_url
        self.rerank_enabled = rerank_enabled
        self.rerank_fetch_k = max(rerank_fetch_k, 1)

        self._embeddings = None
        self._llm = None
        self._vectorstore = None
        self._ingest_lock = threading.Lock()
        self._agent_runner = FunctionalAgentRunner(
            llm_factory=self.get_llm,
            retrieve_documents=self._retrieve_documents,
            format_memory=self._format_memory,
            format_context=self._format_retrieved_context,
        )

    def _chroma_settings(self) -> ChromaSettings:
        return ChromaSettings(
            is_persistent=True,
            persist_directory=str(self.chroma_dir),
            anonymized_telemetry=self.chroma_anonymized_telemetry,
        )

    def _default_headers(self):
        if "openrouter.ai" not in self.base_url:
            return None
        headers = {}
        if self.app_name:
            headers["X-Title"] = self.app_name
        if self.app_url:
            headers["HTTP-Referer"] = self.app_url
        return headers or None

    def _require_api_key(self):
        if not self.api_key:
            raise RuntimeError("API key is not set. Configure AI_API_KEY or the active provider key.")

    def get_embeddings(self):
        if self._embeddings is None:
            self._require_api_key()
            self._embeddings = OpenAIEmbeddings(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.embedding_model,
                timeout=self.ai_timeout_seconds,
                max_retries=self.ai_max_retries,
                default_headers=self._default_headers(),
                # OpenAI-compatible embedding endpoints should receive raw text;
                # local token counting can trigger unsupported tokenizer lookups.
                check_embedding_ctx_length=False,
            )
        return self._embeddings

    def get_llm(self):
        if self._llm is None:
            self._require_api_key()
            self._llm = ChatOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model,
                temperature=0.2,
                timeout=self.ai_timeout_seconds,
                max_retries=self.ai_max_retries,
                default_headers=self._default_headers(),
            )
        return self._llm

    def has_index(self):
        return self.chroma_dir.exists() and any(self.chroma_dir.iterdir())

    def get_vectorstore(self):
        if self._vectorstore is None:
            if not self.has_index():
                raise RuntimeError("Vector index not found. Run ingest first.")
            self._vectorstore = Chroma(
                collection_name="rag",
                persist_directory=str(self.chroma_dir),
                client_settings=self._chroma_settings(),
                embedding_function=self.get_embeddings(),
            )
        return self._vectorstore

    def collect_files(self):
        if not self.data_dir.exists():
            return []
        exts = {".txt", ".md", ".pdf"}
        return [p for p in self.data_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts]

    @staticmethod
    def load_documents(files):
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

    @staticmethod
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

    @staticmethod
    def _format_memory(memory: list[dict[str, str]]) -> str:
        if not memory:
            return "No conversation memory."
        lines = []
        for idx, turn in enumerate(memory[-5:], start=1):
            question = str(turn.get("question", "")).strip()
            answer = str(turn.get("answer", "")).strip()
            if question:
                lines.append(f"{idx}. User: {question}")
            if answer:
                lines.append(f"   Assistant: {answer}")
        return "\n".join(lines) if lines else "No conversation memory."

    @staticmethod
    def _format_retrieved_context(docs: list[Document]) -> str:
        if not docs:
            return "No retrieved context."
        blocks = []
        for idx, doc in enumerate(docs, start=1):
            source = str(doc.metadata.get("source", "unknown"))
            page = doc.metadata.get("page")
            header = f"[{idx}] source={source}"
            if page is not None:
                header += f" page={page}"
            text = (doc.page_content or "").strip().replace("\n", " ")
            if len(text) > 650:
                text = f"{text[:650]}..."
            blocks.append(f"{header}\n{text}")
        return "\n\n".join(blocks)

    def _retrieve_documents(self, question: str, k: int) -> list[Document]:
        started = time.perf_counter()
        top_k = max(int(k), 1)
        vectorstore = self.get_vectorstore()
        fetch_k = max(top_k, self.rerank_fetch_k) if self.rerank_enabled else top_k
        docs = vectorstore.similarity_search(question, k=fetch_k)
        if self.rerank_enabled and docs:
            reranker = EmbeddingRerankService(self.get_embeddings)
            docs = reranker.rerank(question=question, docs=docs, top_k=top_k)
        final_docs = docs[:top_k]
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "rag_retrieval_completed duration_ms=%.2f top_k=%s fetch_k=%s docs=%s",
            elapsed_ms,
            top_k,
            fetch_k,
            len(final_docs),
        )
        return final_docs

    def run_ingest(self, reset: bool):
        with self._ingest_lock:
            files = self.collect_files()
            if not files:
                raise ValueError("No supported files in data/")
            if reset and self.chroma_dir.exists():
                shutil.rmtree(self.chroma_dir)
            docs, failed = self.load_documents(files)
            if not docs:
                raise ValueError("No documents loaded.")
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
            chunks = splitter.split_documents(docs)
            vectorstore = Chroma.from_documents(
                chunks,
                embedding=self.get_embeddings(),
                persist_directory=str(self.chroma_dir),
                collection_name="rag",
                client_settings=self._chroma_settings(),
            )
            self._vectorstore = vectorstore
            return {"files": len(files), "chunks": len(chunks), "failed": failed}

    def answer_question(
        self,
        question: str,
        k: int,
        memory: list[dict[str, str]] | None = None,
        request_id: str | None = None,
    ):
        started = time.perf_counter()
        answer, docs = self._agent_runner.answer(
            question=question,
            k=max(int(k), 1),
            memory=memory or [],
            request_id=request_id,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "rag_answer_completed request_id=%s duration_ms=%.2f k=%s docs=%s memory_turns=%s",
            request_id or "-",
            elapsed_ms,
            max(int(k), 1),
            len(docs),
            len(memory or []),
        )
        return answer, self.build_sources(docs)
