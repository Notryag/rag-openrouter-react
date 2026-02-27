from .db import get_db, now_iso


def get_user_by_id(user_id: int):
    with get_db() as conn:
        return conn.execute(
            "SELECT id, username, password_hash FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


def get_user_by_username(username: str):
    with get_db() as conn:
        return conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()


def create_user(username: str, password_hash: str) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, now_iso()),
        )
        return int(cur.lastrowid)
