from typing import Callable, List

from fastapi import APIRouter, Depends

from schemas.api import SessionCreateRequest, SessionMessage, SessionResponse
from services.session_service import SessionService


def create_session_router(
    session_service: SessionService,
    get_current_user: Callable,
) -> APIRouter:
    router = APIRouter(prefix="/sessions", tags=["sessions"])

    @router.get("", response_model=List[SessionResponse])
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

    @router.post("", response_model=SessionResponse)
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

    @router.get("/{session_id}/messages", response_model=List[SessionMessage])
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

    return router
