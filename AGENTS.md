# Repo Agent Rules

Apply these rules before coding in this repository.

## 1. Architecture First

Read `docs/ARCHITECTURE_RULES.md` before making changes.

Keep new code within the intended layers:
- Backend: `routers/`, `services/`, `repositories/`, `core/`, `schemas/`
- Frontend: `components/`, `hooks/`, `services/`, `state/`

Do not add new business logic to these monolith files:
- `backend/app.py`
- `frontend/src/App.jsx`

If a request conflicts with these rules, explain the conflict and propose a compliant file plan first.

## 2. File Placement

Use the existing layers instead of shortcutting:
- Backend HTTP wiring belongs in `routers/`
- Backend business logic belongs in `services/`
- Backend persistence belongs in `repositories/`
- Frontend fetch/API calls belong in `services/`
- Frontend stateful UI logic belongs in `hooks/` or `state/`
- Frontend composition should stay in `App.jsx`

Do not put new fetch logic directly inside React page components when a frontend service module is the better fit.

## 3. Runbook

Preferred environment:
- Put the repo in a WSL-native path such as `~/workspace/rag-openrouter-react`
- Run both backend and frontend from WSL
- Avoid using a `/mnt/c/...` or `/mnt/d/...` checkout for active frontend development because Vite watch mode is unreliable there

Preferred startup from repo root:

```bash
bash scripts/start_dev.sh
```

If the repo currently lives under `/mnt/...`, migrate it first:

```bash
bash scripts/migrate_to_wsl.sh
```

Manual startup:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

Default local URLs:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## 4. Verification

Run the architecture gate before finalizing:

```bash
python3 scripts/check_architecture.py
```

When relevant, also run the smallest useful check for the area you changed:
- Frontend changes: build or lint if the local Node environment works
- Backend API changes: `python3 backend/scripts/smoke_test.py`
- Backend RAG behavior changes: run the smallest focused smoke path you can justify

If local tooling is broken, state clearly whether the blocker is code-related or environment-related.

## 5. Environment Notes

This repo may be used from WSL and Windows together, but the recommended steady-state workflow is WSL-native only for development.

If an issue appears only when the repo is under `/mnt/...`, treat that as an environment issue first, especially for frontend hot reload and `node_modules`.

Prefer consistent package management in the frontend. If you change frontend dependencies, avoid leaving `package-lock.json` and `pnpm-lock.yaml` out of sync without explanation.

Backend configuration lives in `backend/.env`. If it is missing, copy `backend/.env.example` first.

## 6. Change Discipline

Keep edits focused and minimal.

When changing API shapes or backend behavior, check whether frontend service calls or UI assumptions also need updating.

When adding developer tooling or scripts, place them under `scripts/` unless they are backend-only and clearly belong in `backend/scripts/`.
