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

## Template
- Goal:
- Change:
- Result:
- Risk:
- Next:
