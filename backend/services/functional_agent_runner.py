import threading
import uuid
from typing import Any, Callable, TypedDict

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from langchain_core.documents import Document


class AgentRuntimeContext(TypedDict, total=False):
    question: str
    k: int
    memory: list[dict[str, str]]
    request_id: str


class FunctionalAgentRunner:
    def __init__(
        self,
        llm_factory: Callable[[], Any],
        retrieve_documents: Callable[[str, int], list[Document]],
        format_memory: Callable[[list[dict[str, str]]], str],
        format_context: Callable[[list[Document]], str],
    ):
        self._llm_factory = llm_factory
        self._retrieve_documents = retrieve_documents
        self._format_memory = format_memory
        self._format_context = format_context
        self._agent_lock = threading.Lock()
        self._agent = None
        self._docs_lock = threading.Lock()
        self._retrieved_docs_by_request: dict[str, list[Document]] = {}

    @staticmethod
    def _to_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            chunks = []
            for item in content:
                if isinstance(item, str):
                    chunks.append(item)
                    continue
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        chunks.append(text)
            return "\n".join(part for part in chunks if part)
        return str(content or "")

    @staticmethod
    def _runtime_context_value(request: Any, key: str, default: Any):
        runtime = getattr(request, "runtime", None)
        context = getattr(runtime, "context", None)
        if isinstance(context, dict):
            return context.get(key, default)
        return default

    @staticmethod
    def _coerce_k(raw_k: Any, fallback: int) -> int:
        try:
            return max(int(raw_k), 1)
        except (TypeError, ValueError):
            return max(int(fallback), 1)

    def _latest_user_message(self, request: Any) -> str:
        state = getattr(request, "state", None)
        if not isinstance(state, dict):
            return ""

        messages = state.get("messages", [])
        if not isinstance(messages, list):
            return ""

        for message in reversed(messages):
            role = None
            content = ""
            if isinstance(message, dict):
                role = message.get("role")
                content = self._to_text(message.get("content", ""))
            else:
                role = getattr(message, "role", None) or getattr(message, "type", None)
                content = self._to_text(getattr(message, "content", ""))

            role_text = str(role).lower() if role is not None else ""
            if role_text in {"user", "human"} and content.strip():
                return content.strip()

        return ""

    def _extract_answer_text(self, result: Any) -> str:
        if isinstance(result, dict):
            messages = result.get("messages")
            if isinstance(messages, list):
                for message in reversed(messages):
                    role = None
                    content = ""
                    if isinstance(message, dict):
                        role = message.get("role")
                        content = self._to_text(message.get("content", ""))
                    else:
                        role = getattr(message, "role", None) or getattr(message, "type", None)
                        content = self._to_text(getattr(message, "content", ""))

                    role_text = str(role).lower() if role is not None else ""
                    if role_text in {"assistant", "ai"} and content.strip():
                        return content.strip()

            for key in ("output_text", "answer", "final_output"):
                value = result.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

        return self._to_text(result).strip()

    def _set_request_docs(self, request_id: str, docs: list[Document]):
        if not request_id:
            return
        with self._docs_lock:
            self._retrieved_docs_by_request[request_id] = docs

    def _pop_request_docs(self, request_id: str) -> list[Document]:
        if not request_id:
            return []
        with self._docs_lock:
            return self._retrieved_docs_by_request.pop(request_id, [])

    def _build_agent(self):
        @dynamic_prompt
        def rag_prompt(request: ModelRequest) -> str:
            runtime_question = str(self._runtime_context_value(request, "question", "")).strip()
            active_question = runtime_question or self._latest_user_message(request)

            top_k = self._coerce_k(self._runtime_context_value(request, "k", 4), 4)
            raw_memory = self._runtime_context_value(request, "memory", [])
            active_memory = raw_memory if isinstance(raw_memory, list) else []
            request_id = str(self._runtime_context_value(request, "request_id", "")).strip()

            retrieved_docs: list[Document] = []
            if active_question:
                retrieved_docs = self._retrieve_documents(active_question, top_k)
            self._set_request_docs(request_id, retrieved_docs)

            memory_block = self._format_memory(active_memory)
            context_block = self._format_context(retrieved_docs)
            return (
                "You are a grounded RAG assistant.\n"
                "Use only the retrieved context and conversation memory.\n"
                "If the answer is not supported by context, reply that you don't know.\n\n"
                f"Conversation memory:\n{memory_block}\n\n"
                f"Retrieved context:\n{context_block}"
            )

        return create_agent(
            model=self._llm_factory(),
            tools=[],
            middleware=[rag_prompt],
            context_schema=AgentRuntimeContext,
            name="rag_functional_agent",
        )

    def _get_agent(self):
        if self._agent is None:
            with self._agent_lock:
                if self._agent is None:
                    self._agent = self._build_agent()
        return self._agent

    def answer(
        self,
        question: str,
        k: int,
        memory: list[dict[str, str]] | None = None,
        request_id: str | None = None,
    ) -> tuple[str, list[Document]]:
        safe_memory = memory or []
        active_request_id = (request_id or "").strip() or uuid.uuid4().hex
        top_k = self._coerce_k(k, 4)
        self._set_request_docs(active_request_id, [])
        agent = self._get_agent()
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": question}]},
                context={
                    "question": question,
                    "k": top_k,
                    "memory": safe_memory,
                    "request_id": active_request_id,
                },
            )
        except Exception:
            self._pop_request_docs(active_request_id)
            raise

        docs = self._pop_request_docs(active_request_id)
        return self._extract_answer_text(result), docs
