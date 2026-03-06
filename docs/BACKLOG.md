# BACKLOG

Use this board as the single source of truth for active work.
Rule: keep at most 3 tasks in `doing`.

| Task | Priority | Status | Owner | Notes |
| --- | --- | --- | --- | --- |
| Add auth and per-user sessions | P1 | done | Codex | JWT login + chat history |
| Build RAG eval dataset and script | P1 | done | Codex | 20-50 QA pairs |
| Add tracing and request IDs | P1 | done | Codex | FastAPI middleware + logs |
| Improve ingestion to async job | P2 | done | Codex | queue + worker |
| Establish architecture guardrails + CI gate | P1 | done | Codex | rules doc + check script + workflow |
| Refactor backend monolith (phase 1: schemas + repositories) | P1 | done | Codex | reduce app.py and isolate DB/model concerns |
| Refactor backend monolith (phase 2: services extraction) | P1 | done | Codex | move auth/rag/ingest/session logic to services |
| Refactor backend monolith (phase 3: routers split) | P1 | done | Codex | split routes from app.py into routers modules |
| Add reranker support | P2 | done | Codex | embedding-based rerank with env toggle |
| Add CI checks | P2 | done | Codex | frontend lint/build + backend smoke test in CI |
| Refactor RAG service to singleton Functional Agent middleware flow | P1 | done | Codex | singleton `create_agent` + `@dynamic_prompt` retrieval/context + session memory via invoke context |
| Run live RAG eval baseline and fill metrics | P1 | doing | Codex | real `/chat` eval for current Functional Agent path |

Current notes for `Run live RAG eval baseline and fill metrics`:
- Done 2026-03-06: Trim session memory so historical answers are summarized or truncated before being passed in full to the model.
- Reduce default retrieval depth from `k=4` to `k=2` or `k=3` after validating quality impact.
- Lower per-document retrieved context cap from `650` chars to roughly `300-400`.
- Constrain answer length for summary-style questions, for example `at most 3 bullets and 1 sentence each`.
- Skip retrieval entirely for greeting-style prompts such as `hi` and `hello`.

Status values:
- `todo`
- `doing`
- `done`
