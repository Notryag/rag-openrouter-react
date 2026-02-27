# Repo Agent Rules

Always apply these rules before coding in this repository.

1. Read `docs/ARCHITECTURE_RULES.md` and keep changes within its layering constraints.
2. Do not add new business logic to monolith files:
   - `backend/app.py`
   - `frontend/src/App.jsx`
3. Place new code by layer:
   - Backend: `routers/`, `services/`, `repositories/`, `core/`, `schemas/`
   - Frontend: `components/`, `hooks/`, `services/`, `state/`
4. Run architecture gate before finalizing:
   - `python scripts/check_architecture.py`
5. If a request conflicts with these rules, explain the conflict and propose a compliant file plan first.
