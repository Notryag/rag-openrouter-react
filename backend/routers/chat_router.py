from typing import Callable

from fastapi import APIRouter, Depends, HTTPException

from schemas.api import ChatRequest, ChatResponse
from services.rag_service import RagService
from services.session_service import SessionService


def create_chat_router(
    rag_service: RagService,
    session_service: SessionService,
    get_current_user_optional: Callable,
) -> APIRouter:
    router = APIRouter(tags=["chat"])

    @router.post("/chat", response_model=ChatResponse)
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

    return router
