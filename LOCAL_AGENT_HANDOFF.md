# Enterprise Support Copilot 本地部署交接

> 面向接力部署的本地 Agent / 工程师。目标是把本项目发布到中国大陆可稳定访问的域名，并保持现有交互和诚实的 Demo 边界。

## 1. 交付状态

- 产品名：Enterprise Support Copilot
- 源码版本：`0.4.1`
- 交付基线：V4.1（GSAP 动效、字体可读性、移动端适配、Cloudflare Worker 兼容性修复）
- 技术栈：React 19、Next.js 16、TypeScript、GSAP、Lucide、Vite / Vinext
- 当前形态：完全可离线演示的确定性前端，不依赖 LLM、数据库、向量库或 ERP 服务
- 当前线上站点只用于验收，不应作为中国大陆发布目标

交付 ZIP 解压后，本文件应位于项目根目录。所有命令都从项目根目录执行。

## 2. 产品与数据边界（不得改坏）

这是一个 ERP 故障诊断 Agent 的产品化演示。用户输入问题后，界面展示：

1. 问题理解与分类；
2. 企业知识检索；
3. 只读工具规划与 ERP 查询；
4. 工具证据与引用交叉校验；
5. 结构化根因与建议；
6. 高风险写操作前的 Human-in-the-loop 审批；
7. 可复盘的运行记录与工程视图。

以下声明必须保留：

- 所有企业、用户、单据、日志、知识、工单和耗时均为合成数据。
- 当前版本不调用真实 LLM、RAG、ERP 或生产接口。
- `54 cases`、`91.18% Retrieval hit@3` 等数字是 deterministic baseline，不是生产模型准确率。
- 界面只展示安全的节点摘要、工具输入输出和证据，不展示模型私有 chain-of-thought。
- `create_ticket` 的拒绝路径不能产生写操作；确认后才显示合成工单号，并使用 `run_id` 表达幂等语义。

## 3. 关键文件

| 路径 | 作用 |
| --- | --- |
| `app/SupportConsole.tsx` | 场景数据、播放状态机、证据面板、诊断结果、审批、运行记录、工程视图 |
| `app/globals.css` | 视觉系统、桌面/移动布局、交互和 reduced-motion |
| `app/layout.tsx` | 页面元数据与字体入口 |
| `docs/FULLSTACK_INTEGRATION.md` | 将 fixture 替换为 FastAPI / LangGraph 的接口契约 |
| `FDE_INTERVIEW_PLAYBOOK.md` | 面试讲解、能力映射和问答 |
| `tests/rendered-html.test.mjs` | 服务端首屏、非空证据与动效加载回归测试 |
| `.openai/hosting.json` | 原托管平台项目标识；国内部署不应复用或修改该远端项目 |

## 4. 原始版本验证

要求 Node.js `22.13+`、npm 和 GNU coreutils。先在未修改源码时验证交付物：

```bash
npm ci
npm run lint
npm test
```

期望结果：构建成功，3 个 Node 测试全部通过，Lint 无错误。

如果国内 npm 网络不稳定，可先设置组织允许的 npm 镜像；不要删除 `package-lock.json`，不要用浮动版本重新生成依赖。

## 5. 推荐部署：静态导出到国内对象存储或 Nginx

### 为什么优先静态部署

当前项目只有一个前端路由，数据全部在本地 fixture 中，没有服务端 API、登录或数据库。静态导出拥有最少运行时依赖、最低故障面和最佳中国大陆可达性，也最适合 HR 演示。

### 迁移步骤

在单独部署分支中进行以下修改，不要回写原托管项目：

1. 把构建脚本切换为标准 Next.js：

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint . --ignore-pattern .next --ignore-pattern out"
  }
}
```

保留其余依赖。`vinext`、Cloudflare Vite 插件及 Sites 专用脚本可在部署迁移验证完成后再清理，不要一开始做大规模删改。

2. 将 `next.config.ts` 改为：

```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
```

3. 避免构建期访问 Google Fonts。中国大陆构建环境建议删除 `app/layout.tsx` 中的 `next/font/google` 导入，改用系统字体或随 ZIP 自托管的字体。最小可用写法：

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Enterprise Support Copilot",
  description: "Evidence-grounded ERP incident diagnosis demo.",
  icons: { icon: "/favicon.svg", shortcut: "/favicon.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
```

同时确认 `app/globals.css` 的字体栈含有系统回退，例如：

```css
body {
  font-family: Inter, "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", Arial, sans-serif;
}
```

4. 重新构建并本地验收：

```bash
npm ci
npm run build
npx serve out -l 4173
```

访问 `http://127.0.0.1:4173/`。确认 `out/index.html` 存在，刷新首页仍返回 200，浏览器控制台没有报错，也没有请求 Google Fonts 或原 `chatgpt.site` 域名。

5. 将整个 `out/` 目录上传到以下任一中国大陆可访问目标：

- 阿里云 OSS 静态网站 + CDN；
- 腾讯云 COS 静态网站 + CDN；
- 华为云 OBS 静态网站；
- 已备案域名下的 Nginx 静态目录；
- 公司已有的国内前端托管平台。

对象存储需将默认首页设为 `index.html`，错误页可同样指向 `index.html`。本项目当前只有根路由，不依赖 SPA rewrite。

## 6. 备选部署：国内 VPS 上的 Node / Next.js

如果平台不支持静态网站，使用标准 Next.js standalone：

```ts
// next.config.ts
const nextConfig = {
  output: "standalone",
  images: { unoptimized: true },
};
export default nextConfig;
```

```bash
npm ci
npm run build
HOSTNAME=0.0.0.0 PORT=3000 node .next/standalone/server.js
```

用 systemd、PM2 或容器守护进程，再用 Nginx 反向代理到 `127.0.0.1:3000`，并配置 HTTPS、健康检查和日志轮转。

该方案仍建议移除 `next/font/google`，避免首次构建受跨境网络影响。

## 7. GSAP 与服务端兼容性注意事项

V4.0 曾在 Cloudflare Worker 出现 Error 1101：GSAP 被服务端静态导入后，在 Worker 全局作用域启动计时器。V4.1 已修复为 React 挂载后的浏览器动态加载：

```ts
useEffect(() => {
  void import("gsap").then(({ gsap }) => {
    const context = gsap.context(() => { /* timelines */ }, consoleRef);
    // cleanup calls context.revert()
  });
}, []);
```

部署迁移时不得改回顶层 `import { gsap } from "gsap"` 或 `@gsap/react` 静态注册。`tests/rendered-html.test.mjs` 有相应回归断言。

## 8. 发布验收清单

### 功能

- 首页默认快照中“执行轨迹 / 工具调用 / 知识来源”均有可点击内容。
- 四个场景均可选择并完成播放。
- 诊断结果显示分类、证据置信度、耗时、证据、建议和引用知识。
- 高风险场景的“拒绝”不会显示工单；“确认”显示合成工单号。
- 运行记录可打开任一运行；工程视图的 Code / JSON / Trace 可切换和复制。
- 弹层支持关闭按钮和 Esc。

### 视觉与可达性

- 检查 1440×900、1024×768、390×844、360×800。
- 首页、运行记录和工程视图的标题入场动画正常。
- `prefers-reduced-motion: reduce` 下内容立即可见且无持续动画。
- 键盘 Tab 有可见焦点；移动端底部导航不遮挡内容。
- 所有正文可读，没有小于设计基线的异常字号。

### 网络与发布

- 从中国大陆移动网络和家庭宽带各测试一次。
- 首页与静态资源全部 200；没有跨境字体、脚本、API 或图片请求。
- 强制刷新不出现 404；HTTPS 证书有效；首屏缓存策略合理。
- 使用无痕窗口完成一次完整 Demo。

## 9. 不在本次接力范围内

除非用户明确要求，不要在“部署接力”中顺手实现真实 LLM、登录、数据库、向量检索或 ERP。真实全栈接入应按 `docs/FULLSTACK_INTEGRATION.md` 单独立项，并保留 fixture 作为离线 fallback。

## 10. 部署完成后的交付格式

请回传：

1. 中国大陆可访问的 HTTPS URL；
2. 部署平台、区域和运行方式（静态或 Node）；
3. 最终 Git commit / ZIP 校验值；
4. 桌面与移动端截图；
5. 大陆网络实测结果；
6. 所做源码改动列表；
7. 已知问题与回滚方法。

