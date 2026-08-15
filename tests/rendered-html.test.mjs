import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";

const developmentPreviewMeta =
  /<meta(?=[^>]*\bname=["']codex-preview["'])(?=[^>]*\bcontent=["']development["'])[^>]*>/i;

test("renders development preview metadata", async () => {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  const response = await worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );

  assert.equal(response.status, 200);
  assert.match(
    response.headers.get("content-type") ?? "",
    /^text\/html\b/i,
  );
  const html = await response.text();
  assert.match(html, developmentPreviewMeta);
  assert.match(html, /执行轨迹/);
  assert.match(html, /工具调用/);
  assert.match(html, /知识来源/);
  assert.match(html, /作品演示快照/);
  assert.match(html, /analyze_query/);
  assert.doesNotMatch(html, /尚无执行记录/);
});

test("ships non-empty tool and knowledge fixtures", async () => {
  const source = await readFile(new URL("../app/SupportConsole.tsx", import.meta.url), "utf8");
  assert.match(source, /get_claim_status/);
  assert.match(source, /凭证生成规则/);
  assert.match(source, /REQUEST\\nPOST \/internal\/tools/);
  assert.match(source, /retrieval: hybrid/);
  assert.doesNotMatch(source, /尚无执行记录/);
});

test("ships scoped motion, readable type, and mobile card layout", async () => {
  const [source, css] = await Promise.all([
    readFile(new URL("../app/SupportConsole.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
  ]);
  assert.doesNotMatch(source, /^import .* from ["']gsap["'];?$/m);
  assert.doesNotMatch(source, /@gsap\/react/);
  assert.match(source, /import\("gsap"\)/);
  assert.match(source, /gsap\.context/);
  assert.match(source, /gsap\.matchMedia/);
  assert.match(source, /prefers-reduced-motion: no-preference/);
  assert.match(source, /, consoleRef\)/);
  assert.match(css, /--text-body:\s*14px/);
  assert.match(css, /grid-template-areas:\s*"run arrow" "category risk" "status duration"/);
  assert.match(css, /env\(safe-area-inset-bottom\)/);
});
