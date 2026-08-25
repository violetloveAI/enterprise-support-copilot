import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";

test("ships static first paint with the full demo snapshot", async () => {
  const html = await readFile(
    new URL("../out/index.html", import.meta.url),
    "utf8",
  );

  assert.match(html, /lang=["']zh-CN["']/);
  assert.match(html, /执行轨迹/);
  assert.match(html, /工具调用/);
  assert.match(html, /知识来源/);
  assert.match(html, /作品演示快照/);
  assert.match(html, /analyze_query/);
  assert.doesNotMatch(html, /尚无执行记录/);
  // Static export must not pull cross-border fonts or the legacy hosted origin.
  assert.doesNotMatch(
    html,
    /fonts\.googleapis\.com|fonts\.gstatic\.com|chatgpt\.site/,
  );
});

test("ships non-empty tool and knowledge fixtures", async () => {
  const source = await readFile(new URL("../app/SupportConsole.tsx", import.meta.url), "utf8");
  assert.match(source, /get_claim_status/);
  assert.match(source, /凭证生成规则/);
  assert.match(source, /REQUEST\\nPOST \/internal\/tools/);
  assert.match(source, /retrieval: \$\{scenario\.retrievalLabel/);
  assert.match(source, /scenarioFromApi/);
  assert.match(source, /resumeDiagnosis/);
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
