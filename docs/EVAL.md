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

## Template Row
| YYYY-MM-DD | short change note | 0.00 | 0.00 | 0 | notes |
