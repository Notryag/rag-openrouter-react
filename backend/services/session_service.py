from fastapi import HTTPException

from repositories import session_repository


class SessionService:
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

    @staticmethod
    def get_session(session_id: int):
        return session_repository.get_session_by_id(session_id)

    @staticmethod
    def make_session_title(question: str) -> str:
        cleaned = " ".join(question.split()).strip()
        if not cleaned:
            return "New chat"
        return cleaned[:60]
