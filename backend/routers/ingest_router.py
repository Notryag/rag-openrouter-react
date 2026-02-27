from typing import List

from fastapi import APIRouter, HTTPException

from schemas.api import IngestJobResponse, IngestRequest
from services.ingest_job_service import IngestJobService
from services.rag_service import RagService


def create_ingest_router(
    rag_service: RagService,
    ingest_job_service: IngestJobService,
) -> APIRouter:
    router = APIRouter(prefix="/ingest", tags=["ingest"])

    @router.post("")
    def ingest(payload: IngestRequest):
        try:
            return rag_service.run_ingest(payload.reset)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @router.post("/jobs", response_model=IngestJobResponse)
    def create_ingest_job(payload: IngestRequest):
        job_id = ingest_job_service.create_ingest_job(payload.reset)
        return ingest_job_service.get_ingest_job(job_id)

    @router.get("/jobs", response_model=List[IngestJobResponse])
    def list_ingest_jobs(limit: int = 20):
        return ingest_job_service.list_ingest_jobs(limit)

    @router.get("/jobs/{job_id}", response_model=IngestJobResponse)
    def get_ingest_job(job_id: int):
        return ingest_job_service.get_ingest_job(job_id)

    return router
