# Full-stack integration

The frontend integration is implemented in `app/support-api.ts` and `app/SupportConsole.tsx`.

## Configure

Build or start the frontend with:

```bash
NEXT_PUBLIC_AGENT_API_URL=http://localhost:8000 npm run dev
```

Without this variable the product runs in explicit fixture mode.

## Invoke

`POST /api/v1/chat/invoke`

```json
{ "message": "CLM-2026-005 为什么凭证生成失败？" }
```

The response includes `run_id`, `thread_id`, status, structured diagnosis, retrieved sources, audited tool calls, safe run events, the active model provider and retrieval provider.

## Resume HITL

`POST /api/v1/runs/{run_id}/resume`

```json
{ "decision": "approve" }
```

The backend checks that the run is actually waiting for approval. A rejected run performs no write. An approved run calls the Mock ERP ticket endpoint with the `run_id` as the idempotency key.

## Failure behavior

If a configured Agent API cannot be reached, the frontend displays a visible warning and switches to the deterministic fixture. It never labels fixture content as a live run.
