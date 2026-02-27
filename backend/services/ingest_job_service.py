import json
import threading

from fastapi import HTTPException

from repositories import ingest_job_repository
from schemas.api import IngestJobResponse


class IngestJobService:
    def __init__(self, rag_service, logger):
        self.rag_service = rag_service
        self.logger = logger

    @staticmethod
    def _row_to_ingest_job(row) -> IngestJobResponse:
        failed = []
        raw_failed = row["failed_json"] or "[]"
        try:
            parsed = json.loads(raw_failed)
            if isinstance(parsed, list):
                failed = [str(item) for item in parsed]
        except json.JSONDecodeError:
            failed = [raw_failed]
        return IngestJobResponse(
            id=int(row["id"]),
            status=row["status"],
            reset=bool(row["reset"]),
            files=int(row["files"]),
            chunks=int(row["chunks"]),
            failed=failed,
            error=row["error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _update_ingest_job(job_id: int, **fields):
        ingest_job_repository.update_ingest_job(job_id, **fields)

    def _execute_ingest_job(self, job_id: int, reset: bool):
        self._update_ingest_job(job_id, status="running", error=None)
        try:
            result = self.rag_service.run_ingest(reset)
            self._update_ingest_job(
                job_id,
                status="succeeded",
                files=result["files"],
                chunks=result["chunks"],
                failed_json=json.dumps(result["failed"]),
                error=None,
            )
            self.logger.info(
                "ingest_job_succeeded job_id=%s files=%s chunks=%s",
                job_id,
                result["files"],
                result["chunks"],
            )
        except Exception as exc:
            self._update_ingest_job(
                job_id,
                status="failed",
                error=str(exc),
            )
            self.logger.exception("ingest_job_failed job_id=%s error=%s", job_id, exc)

    def create_ingest_job(self, reset: bool) -> int:
        job_id = ingest_job_repository.create_ingest_job(reset)
        worker = threading.Thread(
            target=self._execute_ingest_job,
            args=(job_id, reset),
            daemon=True,
        )
        worker.start()
        return job_id

    def get_ingest_job(self, job_id: int) -> IngestJobResponse:
        row = ingest_job_repository.get_ingest_job_row(job_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Ingest job not found")
        return self._row_to_ingest_job(row)

    def list_ingest_jobs(self, limit: int = 20):
        rows = ingest_job_repository.list_ingest_job_rows(limit)
        return [self._row_to_ingest_job(row) for row in rows]
