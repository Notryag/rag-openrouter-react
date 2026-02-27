# WORKLOG

Keep entries short. One entry per focused work block.

## 2026-02-27
- Goal: Fix backend import compatibility with latest LangChain packages.
- Change: Updated imports in `backend/app.py`; added missing packages in `backend/requirements.txt`.
- Result: `import app` works and `uvicorn app:app` starts.
- Risk: Runtime quality still needs evaluation set.
- Next: Add a small QA evaluation script and baseline metrics.

## 2026-02-27 (Auth + Sessions)
- Goal: Deliver first P1 backlog item: auth and per-user sessions.
- Change: Added JWT auth endpoints, SQLite user/session/message storage, session APIs, frontend login/session UI, and API token handling.
- Result: Backend import passes, auth/session smoke test passes, frontend build passes.
- Risk: JWT secret in local env is weak by default; production must use >=32-byte secret.
- Next: Build RAG eval dataset and script to establish quality baseline.

## 2026-02-27 (Eval Dataset + Runner)
- Goal: Deliver P1 backlog item for measurable RAG evaluation.
- Change: Added `backend/eval/qa_dataset.jsonl` (20 eval cases) and `backend/scripts/run_eval.py` with dry-run validation and online `/chat` scoring.
- Result: Dry-run dataset validation passed; backend import and runner syntax checks passed.
- Risk: Live score baseline still depends on running backend with valid API key and ingested index.
- Next: Run full eval and fill baseline metrics in `docs/EVAL.md`.

## 2026-02-27 (Tracing + Request IDs)
- Goal: Deliver P1 backlog item for request tracing and IDs.
- Change: Added FastAPI middleware for request ID generation/propagation, latency/status logs, and response `X-Request-ID` header.
- Result: Backend import/compile passed and middleware smoke test confirmed auto + custom request ID behavior.
- Risk: Current tracing is log-based only; no distributed trace backend yet.
- Next: Add CI checks and baseline API smoke tests in pipeline.

## 2026-02-27 (Async Ingest Jobs)
- Goal: Deliver P2 backlog item to decouple ingest from request lifecycle.
- Change: Added `ingest_jobs` persistence, background worker thread execution, and async ingest APIs (`POST/GET /ingest/jobs*`); frontend now polls job status.
- Result: Backend compile/import passed, async ingest smoke test passed, frontend build passed.
- Risk: Worker is process-local; horizontal scaling still needs shared queue/worker.
- Next: Add reranker support with measurable eval impact.

## 2026-02-27 (Architecture Guardrails)
- Goal: Make architecture quality default without repeating prompts every task.
- Change: Added `docs/ARCHITECTURE_RULES.md`, `AGENTS.md`, `scripts/check_architecture.py`, layer skeleton folders, and GitHub CI workflow.
- Result: Architecture check passed locally; backend compile passed; frontend lint/build passed.
- Risk: Legacy files (`backend/app.py`, `frontend/src/App.jsx`) still large; guardrails currently cap growth rather than full split.
- Next: Extract first chunk from monolith files into layer folders in next feature tasks.

## 2026-02-27 (Backend Split Phase 1)
- Goal: Start monolith reduction by extracting schemas and DB repositories from `backend/app.py`.
- Change: Moved API models to `backend/schemas/api.py`; moved DB init and user/session/ingest job SQL operations to `backend/repositories/*`.
- Result: `backend/app.py` reduced from 725 to 520 lines; architecture check passed; backend compile and smoke tests passed.
- Risk: Service/business logic still lives in `app.py`; routers/services split is pending.
- Next: Phase 2 extract auth/ingest/chat logic into `backend/services/`.

## 2026-02-27 (Backend Split Phase 2)
- Goal: Extract business logic from `backend/app.py` into service layer without behavior changes.
- Change: Added `services/auth_service.py`, `services/rag_service.py`, `services/ingest_job_service.py`, `services/session_service.py`; rewired `app.py` to route + dependency composition only.
- Result: `backend/app.py` reduced from 520 to 252 lines; architecture check, compile checks, and API smoke tests passed.
- Risk: Routing is still centralized in `app.py`; next split should move endpoint groups into `routers/`.
- Next: Phase 3 split auth/session/ingest/chat routes into `backend/routers/` modules.

## 2026-02-27 (Backend Split Phase 3)
- Goal: Deliver first todo task by splitting route declarations from `backend/app.py` into `backend/routers/`.
- Change: Added dedicated router modules for auth/session/ingest/chat endpoints and converted `app.py` to composition-only `include_router` wiring.
- Result: Architecture gate passed; backend compile/import checks passed after router extraction.
- Risk: Endpoint behavior still lacks full automated API regression coverage.
- Next: Add reranker support with eval-based quality comparison.

## Template
- Goal:
- Change:
- Result:
- Risk:
- Next:
