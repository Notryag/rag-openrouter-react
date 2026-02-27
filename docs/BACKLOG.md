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
| Add reranker support | P2 | todo | | quality vs latency |
| Add CI checks | P2 | todo | | lint + smoke test |

Status values:
- `todo`
- `doing`
- `done`
