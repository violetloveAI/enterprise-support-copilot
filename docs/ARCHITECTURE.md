# Architecture

## Runtime boundaries

Enterprise Support Copilot uses three independently runnable services:

1. `web`: Next.js workbench. It renders either API data or an explicit offline fixture.
2. `agent-api`: FastAPI + LangGraph. It owns orchestration, retrieval, evidence validation, checkpoints and run events.
3. `mock-erp`: FastAPI + SQLite. It owns synthetic operational records and ticket writes.

The Agent never imports the Mock ERP database module. Production-like reads and writes cross an HTTP boundary through `ERPClient`.

## Graph

```text
START
  -> analyze
      -> clarify -> END
      -> retrieve
          -> plan_tools
              -> execute_tools
                  -> diagnose + evidence_guard
                      -> complete -> END
                      -> approval (interrupt) -> END
                           resume approve -> create_ticket -> END
                           resume reject  -> no side effect -> END
```

## Trust model

- LLM output is a proposal, not an authority.
- Pydantic constrains classification, diagnosis and action shapes.
- The executor accepts only a fixed read-tool allowlist.
- Retrieved content and tool output are treated as untrusted data in prompts.
- Citations outside the current retrieval set are removed.
- Evidence whose `source_id` is not a current chunk or successful current-run tool result is removed.
- Confidence is capped when evidence is missing.
- High-risk output is always escalated.
- `create_ticket` is not exposed to normal tool planning and runs only after graph resume.

## Retrieval

Retrieval and model providers are deliberately independent:

- `RETRIEVAL_PROVIDER=lexical` uses an offline category-aware lexical ranker. It is the deterministic evaluation baseline.
- `RETRIEVAL_PROVIDER=vector` uses Chroma and an OpenAI-compatible embedding endpoint.

This separation allows deterministic model evaluation with vector retrieval, or live model evaluation with reproducible lexical retrieval.

## Persistence

| Store | Owner | Purpose |
|---|---|---|
| `erp.db` | Mock ERP | Synthetic users, claims, flows, vouchers, logs and tickets |
| `copilot.db` | Agent API | Runs and append-only safe events |
| `checkpoints.db` | LangGraph | Pause/resume state for HITL |
| `chroma/` | Retriever | Optional vector collection |

## Public demo boundary

The public static site does not contain a model key. It can show a complete deterministic snapshot without a backend. When `NEXT_PUBLIC_AGENT_API_URL` is supplied at build time, the same UI consumes actual API responses and falls back visibly if the API is unreachable.

