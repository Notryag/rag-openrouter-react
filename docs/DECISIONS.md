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

## Template
- Date:
- Context:
- Decision:
- Tradeoff:
- Revisit trigger:
