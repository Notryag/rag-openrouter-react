# Weekly Operations Notes - 2026-02-20

## Attendees

Alex, Priya, Jordan, Kim

## Key Decisions

1. Increase ingest API rate limit from 500 requests per minute to 800 requests per minute for enterprise tenants.
2. Keep dashboard refresh interval at 5 minutes until cache hit rate improves.
3. Move alert retry policy from 2 attempts to 3 attempts with exponential backoff.

## Action Items

- Priya: publish API limit change notice by 2026-02-24.
- Jordan: benchmark cache layer and report p95 latency.
- Kim: update runbook for alert retry behavior.

## Risks

- High traffic during month-end reporting may increase queue depth.
- Webhook partner endpoints are occasionally slow, causing delayed alert delivery.
