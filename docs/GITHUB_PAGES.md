# GitHub Pages 发布说明

本文只发布前端的离线快照模式。GitHub Pages 不能运行 FastAPI、LangGraph、SQLite 或 Mock ERP。

## 1. 检查现有配置

`next.config.ts` 已配置 `output: "export"`，并由 `GITHUB_PAGES=true` 启用仓库子路径。仓库 Pages 已使用 `gh-pages` 分支根目录，后续发布无需更改此设置。

## 2. 安装发布工具

```bash
npm install --save-dev gh-pages
```

## 3. 构建 Pages 版本

```bash
GITHUB_PAGES=true npm run build -- --webpack
touch out/.nojekyll
```

先在本地检查 `out/` 已生成。不要把后端密钥写入 `NEXT_PUBLIC_*` 环境变量。

## 4. 发布静态目录

```bash
npx gh-pages -d out
```

该命令将 `out/` 发布到 `gh-pages` 分支。

## 5. 首次启用 GitHub Pages（现有仓库可跳过）

1. 打开仓库 **Settings → Pages**。
2. 将 **Source** 设为 **Deploy from a branch**。
3. 选择 `gh-pages` 分支。
4. 选择 `/(root)` 目录。
5. 保存设置。

首次发布完成后，访问：

```text
https://violetloveai.github.io/enterprise-support-copilot/
```

## 6. 发布验收

确认以下结果：

- 首页可以打开。
- 刷新首页不会返回 404。
- CSS、JavaScript 和图片正常加载。
- “演示快照模式”标识可见。
- 桌面端和 `390 × 844` 移动端没有横向溢出。
- 浏览器控制台没有资源路径错误。

如果需要在线运行真实 Agent，请把 Agent API 和 Mock ERP 部署到支持容器的 HTTPS 服务。构建前端时，再将 `NEXT_PUBLIC_AGENT_API_URL` 指向该服务，并更新后端 `CORS_ORIGINS`。

参考：[GitHub Pages 发布源](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)、[Next.js Static Exports](https://nextjs.org/docs/app/guides/static-exports)、[Next.js `basePath`](https://nextjs.org/docs/pages/api-reference/config/next-config-js/basePath)。
