# RAG with OpenRouter (React + FastAPI)

This project provides a small end-to-end RAG setup:
- FastAPI + LangChain backend with persistent Chroma index
- React frontend for ingesting and chatting
- OpenRouter (OpenAI-compatible) API

## Prerequisites
- Python 3.10+
- Node.js 18+

## Backend setup
1) Create `backend/.env`:

```
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-3-small
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
# Optional for OpenRouter analytics
OPENROUTER_APP_NAME=rag-demo
OPENROUTER_APP_URL=http://localhost
JWT_SECRET=replace-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=720
LOG_LEVEL=INFO
```

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
