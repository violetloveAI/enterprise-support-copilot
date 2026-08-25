# Handoff — Full-stack v1.0

## Current state

- The public static experience remains usable without a backend.
- `NEXT_PUBLIC_AGENT_API_URL` switches the same UI to actual FastAPI responses.
- `backend/` contains the LangGraph Agent API, lexical/vector retrieval, evidence guard, independent Mock ERP API, SQLite persistence, tests and evals.
- Default backend mode is deterministic + lexical and needs no secret.
- All business data is synthetic.

## Product rules that must remain true

- Never label fixture output as a live API run.
- Never put a model key in the browser.
- Knowledge citations and tool evidence must belong to the current run.
- No successful tool evidence means no high-confidence system root cause.
- `create_ticket` must remain outside the read-tool allowlist and behind LangGraph interrupt/resume.
- The UI exposes safe summaries and evidence, not private model reasoning.
- Evaluation claims must include dataset, provider and synthetic-baseline boundaries.

## Verification

```bash
npm run test:all
npm run lint
```

For a manual full-stack check, run the three local services from the README, diagnose `CLM-2026-005`, then exercise both approval decisions.

## Next priorities

1. Add model-mode adversarial and failure-case evaluation.
2. Split the large workbench component into domain, fixtures, reducer and presentation modules.
3. Add production identity and authorization design before connecting any real ERP.
4. Deploy the Agent API separately and keep the static fallback.
