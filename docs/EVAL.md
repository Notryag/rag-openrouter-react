# EVAL

Record metric snapshots after each meaningful RAG change.

## Metrics
- `answer_correctness`: percent of answers judged correct on eval set
- `citation_precision`: percent of answers with relevant source citation
- `p95_latency_ms`: p95 API latency for `/chat`
- `avg_cost_usd`: average model cost per answer (optional)

## Baseline
| Date | Change | answer_correctness | citation_precision | p95_latency_ms | Notes |
| --- | --- | --- | --- | --- | --- |
| 2026-02-27 | Initial baseline | TBD | TBD | TBD | Create eval set first |
| 2026-02-27 | Add JWT auth + per-user sessions | TBD | TBD | TBD | Feature-only change; no quality eval run yet |
| 2026-02-27 | Add eval dataset + runner script (20 cases) | TBD | TBD | TBD | Run `backend/scripts/run_eval.py` against live backend to fill numbers |
| 2026-02-27 | Add request tracing + X-Request-ID middleware | TBD | TBD | TBD | Observability change only; quality metrics unchanged |
| 2026-02-27 | Move ingest to async jobs + polling UI | TBD | TBD | TBD | Ingestion architecture change; quality metrics unchanged |
| 2026-02-27 | Add architecture rules + CI architecture gate | TBD | TBD | TBD | Process/maintainability change; quality metrics unchanged |
| 2026-02-27 | Backend split phase 1 (schemas + repositories) | TBD | TBD | TBD | Refactor-only change; quality metrics unchanged |
| 2026-02-27 | Backend split phase 2 (services extraction) | TBD | TBD | TBD | Refactor-only change; quality metrics unchanged |
| 2026-02-27 | Add optional embedding-based reranker | TBD | TBD | TBD | Added quality toggle; run live eval on/off for baseline decision |

## Template Row
| YYYY-MM-DD | short change note | 0.00 | 0.00 | 0 | notes |
