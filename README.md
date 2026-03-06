# RAG with Configurable OpenAI-Compatible Providers (React + FastAPI)

This project provides a small end-to-end RAG setup:
- FastAPI + LangChain backend with persistent Chroma index
- React frontend for ingesting and chatting
- Configurable OpenAI-compatible AI provider support

## Prerequisites
- Python 3.10+
- Node.js 18+

## Recommended development environment

Preferred workflow:
- Keep the repository in a WSL-native path such as `~/workspace/rag-openrouter-react`
- Run both backend and frontend inside WSL
- Open the folder with VS Code Remote WSL

Why:
- Vite file watching and hot reload are much more reliable in WSL-native paths than under `/mnt/c/...` or `/mnt/d/...`
- Mixing Windows-installed frontend dependencies with WSL-installed dependencies leads to unstable `node_modules`

If your current checkout is under `/mnt/...`, migrate it first:

```bash
bash scripts/migrate_to_wsl.sh
```

## Backend setup
1) Create `backend/.env`:

```
AI_PROVIDER=dashscope
AI_API_KEY=your_dashscope_api_key
AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_MODEL=qwen-plus
AI_EMBEDDING_MODEL=text-embedding-v4
AI_APP_NAME=rag-demo
AI_APP_URL=http://localhost
JWT_SECRET=replace-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=720
LOG_LEVEL=INFO
```

Preferred variables are `AI_PROVIDER`, `AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL`, and `AI_EMBEDDING_MODEL`.
Provider-specific fallbacks still work for `DASHSCOPE_*`, `GEMINI_*`, and `OPENROUTER_*`.

2) Install deps and run:

```
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8000
```

## Data ingest
- Put local files in `data/` (`.txt`, `.md`, `.pdf`).
- Frontend now starts an async ingest job and polls status automatically.
- API options:
  - `POST /ingest` (sync, legacy)
  - `POST /ingest/jobs` (create async job)
  - `GET /ingest/jobs/{job_id}` (query status)
  - `GET /ingest/jobs?limit=20` (list recent jobs)

## Evaluation
Dataset and script are included:
- Dataset: `backend/eval/qa_dataset.jsonl` (20 cases)
- Runner: `backend/scripts/run_eval.py`

Examples:
```
cd backend
.\.venv\Scripts\python.exe scripts/run_eval.py --dry-run
.\.venv\Scripts\python.exe scripts/run_eval.py --api-base http://localhost:8000 --k 4
```

## Auth and sessions
- `POST /auth/register` create user
- `POST /auth/login` get bearer token
- `GET /auth/me` validate token
- `GET /sessions` list current user's sessions
- `POST /sessions` create a session
- `GET /sessions/{session_id}/messages` list session history

The frontend stores the bearer token in local storage and automatically sends it for session APIs.

## Request tracing
- Backend middleware logs each request with method, path, status code, and latency.
- Each response includes `X-Request-ID`.
- You can also pass your own `X-Request-ID` header; backend will propagate it.

## Frontend setup
```
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## One-click dev startup
From the repo root:

```bash
bash scripts/start_dev.sh
```

Notes:
- If `backend/.env` does not exist, the script copies `backend/.env.example` and stops so you can fill `AI_API_KEY`.
- If `backend/.venv` or `frontend/node_modules` is missing, the script bootstraps them automatically.
- Default ports are `8000` for backend and `5173` for frontend. In bash you can override them with `BACKEND_PORT=8001 FRONTEND_PORT=5174 bash scripts/start_dev.sh`.
- If you run from `/mnt/...`, the script warns because frontend hot reload may be unreliable there.

## Architecture guardrails
- Human-readable rules: `docs/ARCHITECTURE_RULES.md`
- Machine gate: `python scripts/check_architecture.py`
- Repo agent defaults: `AGENTS.md`

Run locally before commit:
```
python scripts/check_architecture.py
```
