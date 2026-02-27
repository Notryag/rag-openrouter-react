# DECISIONS

Track architecture decisions so future changes are deliberate.

## ADR-001 Local Vector Store with Chroma
- Date: 2026-02-27
- Context: Need a fast local setup for ingestion and retrieval with low ops overhead.
- Decision: Use Chroma local persistence in project directory.
- Tradeoff: Simple local setup, but not ideal for multi-tenant scale.
- Revisit trigger: Concurrent users > 20 or dataset size > 5M chunks.

## ADR-002 OpenRouter as Model Gateway
- Date: 2026-02-27
- Context: Need flexible access to chat and embedding models with one API shape.
- Decision: Use OpenRouter-compatible OpenAI client config.
- Tradeoff: Easy model switching, but vendor dependency for routing and quotas.
- Revisit trigger: Enterprise compliance requirement or strict private model hosting.

## ADR-003 JWT + SQLite for Local Auth and Session History
- Date: 2026-02-27
- Context: Need per-user chat history quickly without adding external infra.
- Decision: Use JWT bearer auth and a local SQLite database (`backend/app.db`) for users, sessions, and messages.
- Tradeoff: Fast to ship and easy local dev, but limited concurrency and no horizontal scaling.
- Revisit trigger: Multi-instance deployment or strict enterprise identity integration.

## ADR-004 JSONL Eval Dataset + Scripted Scoring
- Date: 2026-02-27
- Context: Need repeatable RAG quality checks instead of ad-hoc manual testing.
- Decision: Store eval cases in `backend/eval/qa_dataset.jsonl` and run scoring with `backend/scripts/run_eval.py`.
- Tradeoff: Lightweight and transparent, but keyword-based correctness is coarse and can miss semantic equivalence.
- Revisit trigger: Need model-graded evaluation or larger benchmark coverage.

## ADR-005 Request-ID Middleware for API Tracing
- Date: 2026-02-27
- Context: Need to debug API failures and correlate backend logs with client-side errors.
- Decision: Add FastAPI middleware that emits request completion/failure logs and propagates `X-Request-ID`.
- Tradeoff: Low implementation cost, but still lacks distributed tracing storage/search.
- Revisit trigger: Multi-service architecture or on-call need for cross-service trace views.

## ADR-006 Async Ingest via Job Table + Background Worker
- Date: 2026-02-27
- Context: Synchronous ingest blocks API requests and gives poor UX for larger corpora.
- Decision: Introduce `ingest_jobs` table and background worker thread; expose create/query/list ingest job APIs.
- Tradeoff: Better responsiveness and visibility, but worker is single-process and not distributed.
- Revisit trigger: Need multi-instance deployment or high ingest concurrency.

## ADR-007 Architecture Gate as Default Workflow
- Date: 2026-02-27
- Context: AI changes tended to accumulate logic in monolith files unless repeatedly instructed.
- Decision: Add persistent architecture rules (`docs/ARCHITECTURE_RULES.md`) and enforce via `scripts/check_architecture.py` + CI.
- Tradeoff: Better consistency and maintainability, with stricter constraints that may require small refactors before new feature work.
- Revisit trigger: Monolith files split into layered modules and stricter caps become practical.

## ADR-008 Backend Split Strategy (Incremental, No Behavior Change)
- Date: 2026-02-27
- Context: `backend/app.py` accumulated API models, SQL, business logic, and routing in one file.
- Decision: Use phased extraction: (1) schemas + repositories, (2) services, (3) routers; each phase must preserve behavior and pass smoke tests.
- Tradeoff: More commits and temporary indirection, but much lower regression risk than big-bang rewrite.
- Revisit trigger: If service boundaries become stable and test coverage increases, accelerate to router-level modularization.

## ADR-009 Service Composition in app.py During Transition
- Date: 2026-02-27
- Context: Need to reduce monolith quickly while keeping route behavior stable.
- Decision: Keep `app.py` as composition root that wires `AuthService`, `RagService`, `IngestJobService`, and `SessionService`.
- Tradeoff: Clear separation of business logic, but route declarations are still centralized until router split is complete.
- Revisit trigger: Phase 3 router extraction starts.

## Template
- Date:
- Context:
- Decision:
- Tradeoff:
- Revisit trigger:
