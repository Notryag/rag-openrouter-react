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

## Template
- Goal:
- Change:
- Result:
- Risk:
- Next:
