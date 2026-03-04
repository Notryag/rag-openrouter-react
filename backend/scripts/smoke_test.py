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

from app import app  # noqa: E402
from repositories import db as db_repository  # noqa: E402


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

    print("Smoke test passed: auth/session API flow is healthy.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
