import re

from fastapi import HTTPException

from repositories import session_repository


class SessionService:
    MEMORY_TURN_LIMIT = 5
    MEMORY_QUESTION_CHAR_LIMIT = 180
    MEMORY_ANSWER_CHAR_LIMIT = 280
    MEMORY_SENTENCE_LIMIT = 2

    @classmethod
    def _compact_memory_text(
        cls,
        text: str,
        *,
        char_limit: int,
        sentence_limit: int = 0,
    ) -> str:
        cleaned = " ".join(str(text or "").split()).strip()
        if not cleaned:
            return ""

        if sentence_limit > 0:
            sentences = re.split(r"(?<=[.!?。！？])\s+", cleaned)
            summary = " ".join(part.strip() for part in sentences[:sentence_limit] if part.strip())
            if summary and len(summary) < len(cleaned):
                cleaned = f"{summary} ..."

        if len(cleaned) <= char_limit:
            return cleaned

        clipped = cleaned[: max(char_limit - 3, 1)].rstrip()
        return f"{clipped}..."

    @staticmethod
    def create_session_for_user(user_id: int, title: str) -> int:
        return session_repository.create_session_for_user(user_id, title)

    @staticmethod
    def ensure_session_owner(session_id: int, user_id: int):
        if not session_repository.session_belongs_to_user(session_id, user_id):
            raise HTTPException(status_code=404, detail="Session not found")

    @staticmethod
    def save_message(session_id: int, question: str, answer: str):
        session_repository.save_message(session_id, question, answer)

    @staticmethod
    def list_sessions(user_id: int):
        return session_repository.list_sessions_by_user(user_id)

    @staticmethod
    def list_messages(session_id: int):
        return session_repository.list_messages_by_session(session_id)

    @classmethod
    def build_chat_memory(
        cls,
        session_id: int,
        limit: int = MEMORY_TURN_LIMIT,
    ) -> list[dict[str, str]]:
        rows = session_repository.list_messages_by_session(session_id)
        if limit > 0:
            rows = rows[-limit:]
        return [
            {
                "question": cls._compact_memory_text(
                    row["question"],
                    char_limit=cls.MEMORY_QUESTION_CHAR_LIMIT,
                ),
                "answer": cls._compact_memory_text(
                    row["answer"],
                    char_limit=cls.MEMORY_ANSWER_CHAR_LIMIT,
                    sentence_limit=cls.MEMORY_SENTENCE_LIMIT,
                ),
            }
            for row in rows
        ]

    @staticmethod
    def get_session(session_id: int):
        return session_repository.get_session_by_id(session_id)

    @staticmethod
    def make_session_title(question: str) -> str:
        cleaned = " ".join(question.split()).strip()
        if not cleaned:
            return "New chat"
        return cleaned[:60]
