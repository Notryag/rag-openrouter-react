from .db import get_db, now_iso


def create_ingest_job(reset: bool) -> int:
    timestamp = now_iso()
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO ingest_jobs (status, reset, files, chunks, failed_json, error, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("queued", 1 if reset else 0, 0, 0, "[]", None, timestamp, timestamp),
        )
        return int(cur.lastrowid)


def update_ingest_job(job_id: int, **fields):
    if not fields:
        return
    fields["updated_at"] = now_iso()
    keys = list(fields.keys())
    assignments = ", ".join(f"{key} = ?" for key in keys)
    values = [fields[key] for key in keys]
    values.append(job_id)
    with get_db() as conn:
        conn.execute(
            f"UPDATE ingest_jobs SET {assignments} WHERE id = ?",
            values,
        )


def get_ingest_job_row(job_id: int):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM ingest_jobs WHERE id = ?",
            (job_id,),
        ).fetchone()


def list_ingest_job_rows(limit: int = 20):
    limit = max(1, min(limit, 200))
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM ingest_jobs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
