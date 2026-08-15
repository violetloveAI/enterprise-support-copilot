# Full-stack integration contract

前端 V3 当前使用 `Scenario` fixture 驱动。接入 FastAPI / LangGraph 时应保留该 fixture 作为离线演示 fallback，并把后端事件映射到相同 UI 状态。

## 建议接口

### `POST /api/runs`

请求：

```json
{"query":"今天很多员工提交报销时统一显示 500，发生了什么？"}
```

响应至少包含 `run_id`、`thread_id` 与 `status`。前端随后订阅事件流。

### `GET /api/runs/{run_id}/events`

建议使用 SSE。每条事件包含：

```json
{
  "node": "execute_tools",
  "status": "succeeded",
  "latency_ms": 244,
  "safe_summary": "1/1 calls succeeded",
  "tool_calls": [],
  "citations": []
}
```

只返回可展示的安全摘要，不返回 chain-of-thought。

### `POST /api/runs/{run_id}/approval`

```json
{"action":"create_ticket","decision":"approve","idempotency_key":"RUN-9D42C8"}
```

后端必须再次执行确定性授权检查；不能把前端弹窗视为安全边界。

## UI 状态映射

| 后端状态 | 前端状态 |
| --- | --- |
| 无活动运行 | `idle`，展示最近一次脱敏完整快照 |
| 收到首个事件 | `running`，逐步解锁 Trace / Tools / Knowledge |
| Graph 完成 | `complete`，显示结构化诊断与 JSON |
| Graph interrupt | 打开 HITL 审批弹层 |
| 证据不足 / 工具失败 | 结果卡明确展示不足和下一步，不渲染虚假根因 |

## 兼容性要求

- 保持 `run_id` 与 `thread_id` 的语义分离。
- Tool request/response 必须脱敏并声明 `side_effect`。
- Citation 必须携带文档 ID、chunk ID、score 与校验状态。
- 网络失败时回退到 fixture，并清楚标注 Demo，而不是留下空面板。
