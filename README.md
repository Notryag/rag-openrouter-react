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
```

2) Install deps and run:

```
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

## Data ingest
- Put local files in `data/` (`.txt`, `.md`, `.pdf`).
- Click **Ingest data/** in the UI, or call `POST /ingest`.

## Frontend setup
```
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.
