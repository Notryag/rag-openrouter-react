from .db import get_db, now_iso


def create_session_for_user(user_id: int, title: str) -> int:
    timestamp = now_iso()
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO chat_sessions (user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (user_id, title[:120], timestamp, timestamp),
        )
        return int(cur.lastrowid)


def get_session_by_id(session_id: int):
    with get_db() as conn:
        return conn.execute(
            "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()


def session_belongs_to_user(session_id: int, user_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        ).fetchone()
    return row is not None


def list_sessions_by_user(user_id: int):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM chat_sessions
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        ).fetchall()


def save_message(session_id: int, question: str, answer: str):
    timestamp = now_iso()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO chat_messages (session_id, question, answer, created_at) VALUES (?, ?, ?, ?)",
            (session_id, question, answer, timestamp),
        )
        conn.execute(
            "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
            (timestamp, session_id),
        )


def list_messages_by_session(session_id: int):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT question, answer, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()
