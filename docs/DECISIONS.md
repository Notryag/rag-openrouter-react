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

## Template
- Date:
- Context:
- Decision:
- Tradeoff:
- Revisit trigger:
