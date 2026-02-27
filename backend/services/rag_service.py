import shutil
import threading
from pathlib import Path

from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from services.rerank_service import EmbeddingRerankService


class RagService:
    def __init__(
        self,
        data_dir: Path,
        chroma_dir: Path,
        api_key: str,
        base_url: str,
        model: str,
        embedding_model: str,
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
        self.app_name = app_name
        self.app_url = app_url
        self.rerank_enabled = rerank_enabled
        self.rerank_fetch_k = max(rerank_fetch_k, 1)

        self._embeddings = None
        self._llm = None
        self._vectorstore = None
        self._ingest_lock = threading.Lock()

    def _default_headers(self):
        headers = {}
        if self.app_name:
            headers["X-Title"] = self.app_name
        if self.app_url:
            headers["HTTP-Referer"] = self.app_url
        return headers or None

    def _require_api_key(self):
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")

    def get_embeddings(self):
        if self._embeddings is None:
            self._require_api_key()
            self._embeddings = OpenAIEmbeddings(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.embedding_model,
                default_headers=self._default_headers(),
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
            )
            self._vectorstore = vectorstore
            return {
                "files": len(files),
                "chunks": len(chunks),
                "failed": failed,
            }

    def _build_prompt(self):
        system = (
            "You are a helpful assistant. Answer using only the provided context. "
            "If the answer is not in the context, say you don't know."
        )
        return ChatPromptTemplate.from_messages(
            [("system", system), ("human", "Question: {input}\n\nContext:\n{context}")]
        )

    def _answer_with_rerank(self, question: str, k: int):
        vectorstore = self.get_vectorstore()
        docs = vectorstore.similarity_search(question, k=max(k, self.rerank_fetch_k))
        reranker = EmbeddingRerankService(self.get_embeddings)
        top_docs = reranker.rerank(question=question, docs=docs, top_k=k)
        llm_chain = create_stuff_documents_chain(self.get_llm(), self._build_prompt())
        answer = llm_chain.invoke({"input": question, "context": top_docs})
        return answer, self.build_sources(top_docs)

    def answer_question(self, question: str, k: int):
        if self.rerank_enabled:
            return self._answer_with_rerank(question=question, k=k)

        vectorstore = self.get_vectorstore()
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        combine_docs_chain = create_stuff_documents_chain(self.get_llm(), self._build_prompt())
        retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)
        result = retrieval_chain.invoke({"input": question})
        docs = result.get("context", [])
        answer = result.get("answer", "")
        return answer, self.build_sources(docs)
