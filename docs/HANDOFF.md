# Handoff — Frontend Demo v0.4.1

## Status

V4.1 已完成：在 V3 非空证据链基础上，加入 GSAP 分层动效、可读字体系统和完整移动端布局，并修复 GSAP 静态导入导致的 Cloudflare Worker Error 1101。

## Primary code

- `app/SupportConsole.tsx`: scenario schema、播放状态机、执行轨迹、工具与知识详情、诊断结果、审批结果、运行记录和工程视图。
- `app/SupportConsole.tsx`: GSAP 在浏览器挂载后动态加载；timeline selector 限制在 `consoleRef` 内，并使用 matchMedia / context cleanup。不要改回服务端静态导入。
- `app/page.tsx`: route entry。
- `app/globals.css`: visual tokens, three-column console, responsive breakpoints, focus states, and motion rules.
- `app/layout.tsx`: production title, description, locale, and fonts.

## Important product rules preserved

- Demo Mode is the default and is explicitly disclosed as synthetic.
- 指标明确标注为 deterministic baseline，不代表生产模型准确率。
- Retrieved knowledge and tool evidence are visible.
- Private chain-of-thought is not displayed.
- `create_ticket` requires deterministic human confirmation.
- Cancel executes no write action; confirm returns a synthetic incident ID.

## Verification checklist

- Build the project with `npm run build`，再执行 `npm test` 与 `npm run lint`。
- 在 idle 状态切换 Trace / Tools / Knowledge，确认每个标签均有可点击内容。
- 执行四个场景中的至少一个，确认节点按阶段解锁。
- 测试高风险场景的拒绝与确认路径。
- 检查 1440px 与窄屏布局，并确认 Esc 可关闭详情和审批弹层。
- 检查 reduced-motion：页面应立即显示最终状态，不应遗留隐藏元素或持续动画。

## Next implementation step

按 `docs/FULLSTACK_INTEGRATION.md` 接入 FastAPI SSE/JSON 响应，保持 UI fixture 作为离线 fallback；不要删除默认快照，否则作品集首次打开会重新出现空白证据面板。

中国大陆部署接力优先阅读根目录 `LOCAL_AGENT_HANDOFF.md`。

## Known limitations

- 当前托管版本未连接真实 backend、embedding、vector store 或 live LLM。
- 延迟数据是合成运行快照，不是生产测量值。
- `SupportConsole.tsx` 是当前产品体验的权威实现；README 与旧 V1 描述已在 V3 更新。
