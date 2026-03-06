#!/usr/bin/env python3
"""Run a minimal backend API smoke test without external services."""

from __future__ import annotations

import sys
import tempfile
import uuid
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app as backend_app_module  # noqa: E402
from repositories import db as db_repository  # noqa: E402

app = backend_app_module.app


def assert_status(actual: int, expected: int, context: str):
    if actual != expected:
        raise AssertionError(f"{context}: expected {expected}, got {actual}")


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="api-smoke-db-") as tmp:
        db_repository.AUTH_DB_PATH = Path(tmp) / "app.db"

        with TestClient(app) as client:
            no_auth = client.get("/auth/me")
            assert_status(no_auth.status_code, 401, "GET /auth/me without token")
            if not no_auth.headers.get("X-Request-ID"):
                raise AssertionError("Expected X-Request-ID header on unauthorized response")

            username = f"smoke_{uuid.uuid4().hex[:8]}"
            password = "smoke-password-123"

            register = client.post(
                "/auth/register",
                json={"username": username, "password": password},
            )
            assert_status(register.status_code, 200, "POST /auth/register")
            if register.json().get("username") != username:
                raise AssertionError("Register response username mismatch")

            login = client.post(
                "/auth/login",
                json={"username": username, "password": password},
            )
            assert_status(login.status_code, 200, "POST /auth/login")
            token = login.json().get("access_token")
            if not token:
                raise AssertionError("Login response missing access_token")

            headers = auth_headers(token)
            me = client.get("/auth/me", headers=headers)
            assert_status(me.status_code, 200, "GET /auth/me with token")
            if me.json().get("username") != username:
                raise AssertionError("Auth me response username mismatch")

            create_session = client.post(
                "/sessions",
                json={"title": "Smoke Session"},
                headers=headers,
            )
            assert_status(create_session.status_code, 200, "POST /sessions")
            session_id = create_session.json().get("id")
            if not isinstance(session_id, int):
                raise AssertionError("Session create response missing integer id")

            list_sessions = client.get("/sessions", headers=headers)
            assert_status(list_sessions.status_code, 200, "GET /sessions")
            if not any(item.get("id") == session_id for item in list_sessions.json()):
                raise AssertionError("Created session not found in list")

            list_messages = client.get(f"/sessions/{session_id}/messages", headers=headers)
            assert_status(list_messages.status_code, 200, "GET /sessions/{id}/messages")
            if list_messages.json() != []:
                raise AssertionError("Expected no messages in new session")

            original_answer_question = backend_app_module.rag_service.answer_question
            chat_calls: list[dict[str, object]] = []

            def fake_answer_question(
                question: str,
                k: int,
                memory: list[dict[str, str]] | None = None,
                request_id: str | None = None,
            ):
                chat_calls.append(
                    {
                        "question": question,
                        "k": k,
                        "memory": memory or [],
                        "request_id": request_id,
                    }
                )
                return "stubbed answer", [{"source": "smoke-test"}]

            backend_app_module.rag_service.answer_question = fake_answer_question
            try:
                first_chat = client.post(
                    "/chat",
                    json={"question": "First smoke question", "k": 2},
                    headers=headers,
                )
                assert_status(first_chat.status_code, 200, "POST /chat first turn")
                first_session_id = first_chat.json().get("session_id")
                if not isinstance(first_session_id, int):
                    raise AssertionError("Expected first chat to create a session id")

                second_chat = client.post(
                    "/chat",
                    json={
                        "question": "Follow-up smoke question",
                        "k": 3,
                        "session_id": first_session_id,
                    },
                    headers=headers,
                )
                assert_status(second_chat.status_code, 200, "POST /chat follow-up turn")
            finally:
                backend_app_module.rag_service.answer_question = original_answer_question

            if len(chat_calls) != 2:
                raise AssertionError("Expected two captured chat calls")

            if chat_calls[0]["memory"] != []:
                raise AssertionError("Expected first chat call to have empty memory")

            second_memory = chat_calls[1]["memory"]
            if not isinstance(second_memory, list) or len(second_memory) != 1:
                raise AssertionError("Expected follow-up chat call to receive one memory turn")

            first_turn = second_memory[0]
            if first_turn.get("question") != "First smoke question":
                raise AssertionError("Follow-up memory question mismatch")
            if first_turn.get("answer") != "stubbed answer":
                raise AssertionError("Follow-up memory answer mismatch")
            if not chat_calls[1]["request_id"]:
                raise AssertionError("Expected request_id to be forwarded to rag service")

    print("Smoke test passed: auth/session/chat API flow is healthy.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
