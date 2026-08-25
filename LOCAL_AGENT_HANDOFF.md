# Enterprise Support Copilot 本地交接

## 当前交付

- 版本：1.0.0
- 前端：Next.js 16 / React 19 / TypeScript
- 后端：FastAPI / LangGraph / lexical 或 vector retrieval / SQLite
- 集成：独立 Mock ERP REST API、审计事件、证据门、HITL 工单审批
- 数据：全部为合成数据

公开站点可以纯静态运行；本地或独立部署时，通过 `NEXT_PUBLIC_AGENT_API_URL` 连接真实 Agent API。API 不可用时前端会明确提示并降级到 fixture。

## 验证

```bash
npm ci
cd backend && uv sync --extra dev && cd ..
npm run test:all
npm run lint
```

## 启动

最简单的方式：

```bash
docker compose up --build
```

或者按 README 分别启动 Mock ERP、Agent API 和前端。

## 发布边界

- 静态站点不保存任何模型密钥。
- 如需公开真实 API 模式，后端必须单独部署并限制 CORS、速率与日志敏感字段。
- 当前没有 SSO、RBAC、租户隔离或真实 ERP 授权，不得描述成生产系统。
- `.openai/hosting.json` 属于现有 Sites 项目，不要创建第二个站点项目。

完整架构和接口见 `docs/ARCHITECTURE.md`、`docs/FULLSTACK_INTEGRATION.md`。

