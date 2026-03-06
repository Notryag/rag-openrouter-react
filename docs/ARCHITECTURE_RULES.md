# Architecture Rules

This file defines the default coding architecture for this repository.

## Goal
- Prevent monolithic files from growing.
- Keep backend and frontend layered and testable.
- Make AI output stable without repeating long prompts every time.

## Backend Rules
- Target layout:
  - `backend/routers/` HTTP endpoint wiring only
  - `backend/services/` business logic
  - `backend/repositories/` DB access
  - `backend/core/` config, logging, security
  - `backend/schemas/` request/response models
- `backend/app.py` is legacy composition/wiring only.
- Route handlers should live in `backend/routers/` modules and be mounted via `app.include_router(...)`.
- New business logic should not be added to `backend/app.py`.
- New `.py` source files should be placed under the layer folders above (or `backend/scripts/` for tooling scripts).

## RAG Agent Rules
- RAG answer path must use Functional Agent mode based on `create_agent`.
- Retrieval, memory formatting, and context injection must be implemented in `@dynamic_prompt` middleware.
- Do not use legacy `langchain.chains` APIs in backend code (for example `RetrievalQA`, `create_retrieval_chain`, `create_stuff_documents_chain`).
- Agent instance should be created once per service lifecycle and reused across requests; request-specific data must flow via invoke-time context/state.

## Frontend Rules
- Target layout:
  - `frontend/src/components/` UI components
  - `frontend/src/hooks/` stateful UI logic
  - `frontend/src/services/` API clients
  - `frontend/src/state/` shared app state
- `frontend/src/App.jsx` should remain a composition container.
- New business logic should not be added to `App.jsx` or `api.js`.

## Size Guardrails
- Temporary max lines (hard gate in CI):
  - `backend/app.py <= 740`
  - `frontend/src/App.jsx <= 330`
  - Other backend `.py` files `<= 260`
  - Other frontend `.js/.jsx` files `<= 220`
- These caps are transitional and should be reduced as refactoring progresses.

## CI Gate
- Run `python scripts/check_architecture.py`.
- Backend API changes should include a smoke path in CI (`python backend/scripts/smoke_test.py`).
- Any violation fails CI and should be fixed before merging.

## Refactor Policy
- Feature work can proceed, but every large task should include at least one extraction step:
  - Move one chunk from monolith file to proper layer.
  - Keep behavior unchanged for extraction commits.
