# Enterprise Support Copilot — Delivery Plan

## Goal

Build a portfolio-grade enterprise support console that makes knowledge retrieval, system evidence, structured diagnosis, and human approval visible without exposing private chain-of-thought.

## Scope

### Milestone 1 — Interactive frontend demo (complete)

- Four deterministic synthetic ERP scenarios
- Workbench, run history, engineering view, and diagnosis panel
- Six-node Analyze → Retrieve → Plan → Execute → Guard → Compose playback
- Non-empty default snapshot with expandable trace, tool, and citation evidence
- Deterministic approval gate for the P1 write action
- Responsive layout, keyboard focus, and reduced-motion support
- Public deployment and complete source handoff

### Milestone 2 — Mock ERP and real RAG

- FastAPI + SQLite synthetic ERP
- Six REST endpoints and 20–30 diagnostic records
- 10–12 Chinese Markdown knowledge documents
- Ingestion, chunking, embeddings, vector retrieval, citations
- Five read-only tools and one policy-gated write tool
- Structured diagnosis API consumed by this frontend

### Milestone 3 — Agent workflow and evaluation

- Explainable LangGraph workflow
- Live AI mode with graceful no-key fallback
- Structured JSON logging and optional LangSmith tracing
- 30–50 case evaluation dataset and honest generated metrics
- Evaluation page reading real results only

## Design decisions

- Enterprise SaaS visual system: dark mineral header, warm white surfaces, restrained teal accent.
- Motion explains state changes and provides input feedback; common actions stay fast and subtle.
- Demo Mode is explicitly labeled as synthetic and pre-recorded.
- The interface shows workflow events and evidence, never private chain-of-thought.

## Current limitations

- Milestone 1 uses deterministic fixtures; no backend or model call is made.
- Evaluation numbers describe the repository's deterministic baseline, not production model accuracy.
- The hosted V3 is a frontend fixture experience until Milestone 2 APIs are connected.
