"use client";

import {
  Activity, ArrowUp, BookOpen, Bot, Braces, Check, ChevronRight,
  CircleDot, Clipboard, Code2, Copy, Database, FileJson, History,
  Home, Layers3, Plus, ShieldCheck, Sparkles, Terminal,
  TicketCheck, Wrench, X, Zap,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  hasConfiguredApi,
  invokeDiagnosis,
  resumeDiagnosis,
  type ApiRunResponse,
} from "./support-api";

type View = "workbench" | "runs" | "engineering";
type DetailTab = "trace" | "tools" | "knowledge";
type EngineeringTab = "code" | "json" | "trace";
type TraceEvent = {
  node: string; label: string; caption: string; latency: number; output: string;
};
type Scenario = {
  id: string; title: string; question: string; caption: string; claim: string;
  category: string; risk: "低风险" | "中风险" | "高风险"; confidence: number;
  duration: string; rootCause: string; evidence: string; needsApproval: boolean;
  steps: string[]; sources: { id: string; title: string; score: number; excerpt: string }[];
  tools: { name: string; latency: number; request: string; response: string }[];
  trace?: TraceEvent[];
  runtime?: "fixture" | "api";
  retrievalLabel?: string;
  ticketId?: string;
};

const scenarios: Scenario[] = [
  {
    id: "voucher", title: "凭证生成失败", claim: "CLM-2026-005", caption: "财务期间配置异常",
    question: "CLM-2026-005 为什么凭证生成失败？", category: "凭证 / 配置问题",
    risk: "中风险", confidence: 92, duration: "1.18s", needsApproval: true,
    rootCause: "财务期间未开放，凭证生成被配置校验拦截。",
    evidence: "凭证服务返回 FI_PERIOD_CLOSED；公司代码 C100 的 2026-08 期间状态为 CLOSED。",
    steps: ["核对公司代码与计划过账日期", "由财务控制岗确认期间开放策略", "配置修复后由授权人员重新触发凭证"],
    sources: [
      { id: "KB-008", title: "凭证生成规则", score: 94, excerpt: "凭证生成前必须校验公司代码、过账日期与财务期间状态。" },
      { id: "KB-009", title: "财务期间与科目配置规范", score: 89, excerpt: "关闭期间禁止新凭证过账，开放操作需由财务控制岗执行。" },
      { id: "KB-012", title: "运维升级 SOP", score: 84, excerpt: "涉及财务配置变更时，创建工单并要求授权人确认。" },
    ],
    tools: [
      { name: "get_claim_status", latency: 86, request: '{"claim_id":"CLM-2026-005"}', response: '{"status":"APPROVED","company_code":"C100"}' },
      { name: "get_voucher_status", latency: 112, request: '{"claim_id":"CLM-2026-005"}', response: '{"status":"FAILED","error":"FI_PERIOD_CLOSED"}' },
    ],
  },
  {
    id: "sync", title: "附件同步超时", claim: "CLM-2026-007", caption: "接口连续失败",
    question: "CLM-2026-007 附件同步接口为什么失败？", category: "接口 / 系统异常",
    risk: "高风险", confidence: 95, duration: "1.42s", needsApproval: true,
    rootCause: "附件服务连接池耗尽，重试任务持续超时。",
    evidence: "近 15 分钟出现 38 次 HTTP 504；attachment-sync 依赖平均响应时间达到 12.4s。",
    steps: ["确认附件服务健康状态与连接池", "暂停非必要批量同步任务", "创建 P1 工单并通知接口值班组"],
    sources: [
      { id: "KB-010", title: "ERP 接口排查手册", score: 96, excerpt: "同一依赖连续 5xx 或超时应按共享服务异常处理。" },
      { id: "KB-012", title: "运维升级 SOP", score: 93, excerpt: "核心提交链路大面积失败时需升级为 P1。" },
      { id: "KB-011", title: "常见问题 FAQ", score: 81, excerpt: "附件任务允许重试，但不得绕过病毒扫描与权限校验。" },
    ],
    tools: [
      { name: "get_claim_status", latency: 74, request: '{"claim_id":"CLM-2026-007"}', response: '{"status":"DRAFT","attachment_count":4}' },
      { name: "get_interface_log", latency: 138, request: '{"claim_id":"CLM-2026-007","window":"15m"}', response: '{"failures":38,"status":504,"dependency":"attachment-sync"}' },
    ],
  },
  {
    id: "permission", title: "差旅权限缺失", claim: "U1002", caption: "提交动作被拒绝",
    question: "用户 U1002 提交差旅报销时提示没有权限", category: "权限问题",
    risk: "低风险", confidence: 97, duration: "0.84s", needsApproval: false,
    rootCause: "用户具备登录与草稿权限，但缺少 expense.travel.submit。",
    evidence: "角色 Expense-Employee 已分配；权限集合中不存在 expense.travel.submit。",
    steps: ["核对员工组织与成本中心", "由直属主管发起权限申请", "授权后重新登录并验证提交动作"],
    sources: [
      { id: "KB-003", title: "用户权限管理规范", score: 97, excerpt: "登录权限与业务提交权限独立管理。" },
      { id: "KB-004", title: "报销角色权限矩阵", score: 92, excerpt: "差旅提交需要 expense.travel.submit 权限。" },
      { id: "KB-007", title: "员工与成本中心主数据", score: 78, excerpt: "角色分配前需确认有效组织归属。" },
    ],
    tools: [
      { name: "get_user_permissions", latency: 91, request: '{"user_id":"U1002"}', response: '{"roles":["Expense-Employee"],"missing":["expense.travel.submit"]}' },
    ],
  },
  {
    id: "outage", title: "公司范围 500", claim: "INC-SCOPE", caption: "多用户同时失败",
    question: "今天很多员工提交报销时统一显示 500，发生了什么？", category: "接口 / 系统异常",
    risk: "高风险", confidence: 93, duration: "1.36s", needsApproval: true,
    rootCause: "主数据依赖持续超时，造成报销提交服务公司范围不可用。",
    evidence: "15 分钟内记录 127 次同源 500；多个用户、多个成本中心均受影响。",
    steps: ["冻结报销服务非必要发布", "检查主数据依赖与最近变更", "创建 P1 事件并通知 ERP 值班组"],
    sources: [
      { id: "KB-010", title: "ERP 接口排查手册", score: 95, excerpt: "多用户同源 5xx 优先判断共享依赖异常。" },
      { id: "KB-012", title: "运维升级 SOP", score: 94, excerpt: "公司范围核心能力不可用符合 P1 标准。" },
      { id: "KB-011", title: "常见问题 FAQ", score: 82, excerpt: "不要让用户反复提交，以免放大队列压力。" },
    ],
    tools: [
      { name: "get_interface_log", latency: 151, request: '{"scope":"expense-submit","window":"15m"}', response: '{"failures":127,"status":500,"dependency":"master-data"}' },
    ],
  },
];

const traceStages = [
  ["理解问题", "提取业务实体与故障意图", 42],
  ["检索知识", "召回制度、FAQ 与 SOP", 128],
  ["规划工具", "根据证据缺口选择接口", 18],
  ["执行查询", "调用模拟 ERP REST API", 244],
  ["生成诊断", "交叉验证证据并评估风险", 612],
] as const;

const navItems: { id: View; label: string; icon: typeof Home }[] = [
  { id: "workbench", label: "诊断工作台", icon: Home },
  { id: "runs", label: "运行记录", icon: History },
  { id: "engineering", label: "工程视图", icon: Code2 },
];

function getRunId(id: string) {
  return id === "voucher" ? "RUN-8F21A4" : id === "sync" ? "RUN-3C77D9" : id === "permission" ? "RUN-6A10E2" : "RUN-9D42C8";
}

function getTraceEvents(scenario: Scenario): TraceEvent[] {
  if (scenario.trace?.length) return scenario.trace;
  return [
    {
      node: "analyze_query", label: "理解问题", caption: `识别 ${scenario.claim} · ${scenario.category}`,
      latency: 42, output: `intent: diagnose_support_issue\nentity: ${scenario.claim}\ncategory: ${scenario.category}\nmissing_context: []`,
    },
    {
      node: "retrieve_knowledge", label: "检索知识", caption: `从 enterprise-kb 召回 Top ${scenario.sources.length}`,
      latency: 128, output: `query: ${scenario.question}\ncollection: enterprise-kb\ntop_k: 3\nhits: ${scenario.sources.map((source) => `${source.id}(${source.score / 100})`).join(", ")}`,
    },
    {
      node: "plan_tools", label: "规划工具", caption: `选择 ${scenario.tools.length} 个只读 ERP 工具`,
      latency: 18, output: `policy: READ_ONLY_FIRST\nselected_tools:\n${scenario.tools.map((tool) => `  - ${tool.name}`).join("\n")}\nwrite_tools: []`,
    },
    {
      node: "execute_tools", label: "执行查询", caption: `${scenario.tools.length}/${scenario.tools.length} 调用成功 · 无重试`,
      latency: 244, output: scenario.tools.map((tool) => `${tool.name}  200 OK  ${tool.latency} ms`).join("\n"),
    },
    {
      node: "evidence_guard", label: "证据校验", caption: "工具证据与知识引用通过一致性检查",
      latency: 31, output: `grounded: true\nvalid_citations: ${scenario.sources.map((source) => source.id).join(", ")}\nunsupported_claims: 0\nconfidence: ${scenario.confidence / 100}`,
    },
    {
      node: "compose_answer", label: "生成诊断", caption: `${scenario.risk} · ${scenario.needsApproval ? "建议 HITL 升级" : "无需写操作"}`,
      latency: 612, output: `root_cause: ${scenario.rootCause}\nrisk: ${scenario.risk}\nescalation_required: ${scenario.needsApproval}\nrecommended_steps: ${scenario.steps.length}`,
    },
  ];
}

const eventLabels: Record<string, [string, string]> = {
  analyze: ["理解问题", "结构化问题与业务实体"],
  clarify: ["补充信息", "检测必要字段是否缺失"],
  retrieve: ["检索知识", "召回可引用的制度与手册"],
  plan_tools: ["规划工具", "只选择必要的只读 ERP 工具"],
  execute_tools: ["执行查询", "通过 REST 边界读取合成 ERP"],
  diagnose: ["生成诊断", "证据校验、风险判断与处置建议"],
  approval: ["人工审批", "写操作前暂停并等待明确决策"],
};

function scenarioFromApi(run: ApiRunResponse, fallback: Scenario): Scenario {
  const diagnosis = run.diagnosis;
  if (!diagnosis) return fallback;
  const riskMap = { low: "低风险", medium: "中风险", high: "高风险" } as const;
  const toolLatency = new Map(
    run.events
      .filter((event) => event.event_type === "tool_result")
      .map((event) => [String(event.details.tool_name ?? ""), event.duration_ms ?? 0]),
  );
  const durationMs = run.events.reduce((sum, event) => sum + (event.duration_ms ?? 0), 0);
  const trace = run.events
    .filter((event) => event.node_name && event.node_name !== "invoke")
    .map((event) => {
      const [label, caption] = eventLabels[event.node_name] ?? [event.node_name, event.event_type];
      return {
        node: `${event.node_name}:${event.sequence}`,
        label,
        caption,
        latency: event.duration_ms ?? 0,
        output: JSON.stringify(event.details, null, 2),
      };
    });
  return {
    ...fallback,
    category: diagnosis.category_label,
    risk: riskMap[diagnosis.risk_level],
    confidence: Math.round(diagnosis.confidence * 100),
    duration: `${Math.max(durationMs, 1)}ms`,
    rootCause: diagnosis.possible_causes[0] ?? diagnosis.uncertainty_statement ?? "证据不足，无法确认根因。",
    evidence: diagnosis.evidence.map((item) => item.statement).join("；") || diagnosis.uncertainty_statement || "当前没有可验证的工具证据。",
    needsApproval: diagnosis.escalation_required,
    steps: diagnosis.troubleshooting_steps,
    sources: run.retrieved_sources.map((source) => ({
      id: source.chunk_id,
      title: source.title,
      score: Math.round(source.score * 100),
      excerpt: source.content,
    })),
    tools: run.tool_calls.map((tool) => ({
      name: tool.tool_name,
      latency: toolLatency.get(tool.tool_name) ?? 0,
      request: JSON.stringify(tool.arguments),
      response: JSON.stringify(tool.ok ? tool.result : { error: tool.error }),
    })),
    trace,
    runtime: "api",
    retrievalLabel: run.retrieval_provider === "vector" ? "Vector retrieval" : "Lexical retrieval",
    ticketId: run.ticket && typeof run.ticket.ticket_id === "string" ? run.ticket.ticket_id : undefined,
  };
}

function prettyJson(value: string) {
  try { return JSON.stringify(JSON.parse(value), null, 2); } catch { return value; }
}

export default function SupportConsole() {
  const consoleRef = useRef<HTMLDivElement>(null);
  const [view, setView] = useState<View>("workbench");
  const [scenarioId, setScenarioId] = useState("voucher");
  const [query, setQuery] = useState("");
  const [runState, setRunState] = useState<"idle" | "running" | "complete">("idle");
  const [stage, setStage] = useState(0);
  const [detailTab, setDetailTab] = useState<DetailTab>("trace");
  const [engTab, setEngTab] = useState<EngineeringTab>("code");
  const [modal, setModal] = useState<{ title: string; subtitle: string; body: string; code?: boolean } | null>(null);
  const [approvalOpen, setApprovalOpen] = useState(false);
  const [ticketStatus, setTicketStatus] = useState<"idle" | "created" | "rejected">("idle");
  const [checkedSteps, setCheckedSteps] = useState<number[]>([]);
  const [copied, setCopied] = useState(false);
  const [runResponse, setRunResponse] = useState<ApiRunResponse | null>(null);
  const [runtimeMode, setRuntimeMode] = useState<"fixture" | "configured" | "api" | "fallback">(
    hasConfiguredApi() ? "configured" : "fixture",
  );
  const [runError, setRunError] = useState<string | null>(null);
  const [approvalPending, setApprovalPending] = useState(false);
  const timers = useRef<Array<ReturnType<typeof setTimeout>>>([]);
  const baseScenario = scenarios.find((item) => item.id === scenarioId) ?? scenarios[0];
  const scenario = runResponse ? scenarioFromApi(runResponse, baseScenario) : baseScenario;
  const runId = runResponse?.run_id ?? getRunId(scenario.id);

  useEffect(() => {
    let disposed = false;
    let cleanup: (() => void) | undefined;
    void import("gsap").then(({ gsap }) => {
      if (disposed || !consoleRef.current) return;
      const context = gsap.context(() => {
        const media = gsap.matchMedia();
        media.add(
          { motion: "(prefers-reduced-motion: no-preference)", desktop: "(min-width: 861px)" },
          (match) => {
            if (!match.conditions?.motion) return;
            const distance = match.conditions.desktop ? 18 : 10;
            const timeline = gsap.timeline({ defaults: { duration: 0.58, ease: "power3.out" } });
            timeline
              .fromTo(".app-sidebar > *", { autoAlpha: 0, x: -distance }, { autoAlpha: 1, x: 0, stagger: 0.055, clearProps: "transform,opacity,visibility" })
              .fromTo(".app-header > *", { autoAlpha: 0, y: -10 }, { autoAlpha: 1, y: 0, stagger: 0.08, clearProps: "transform,opacity,visibility" }, 0.08)
              .fromTo(".evidence-panel", { autoAlpha: 0, x: distance }, { autoAlpha: 1, x: 0, clearProps: "transform,opacity,visibility" }, 0.18);
          },
        );
        cleanup = () => media.revert();
      }, consoleRef);
      const mediaCleanup = cleanup;
      cleanup = () => { mediaCleanup?.(); context.revert(); };
    });
    return () => { disposed = true; cleanup?.(); };
  }, []);

  useEffect(() => {
    let disposed = false;
    let cleanup: (() => void) | undefined;
    void import("gsap").then(({ gsap }) => {
      if (disposed || !consoleRef.current) return;
      const context = gsap.context(() => {
        const media = gsap.matchMedia();
        media.add(
          { motion: "(prefers-reduced-motion: no-preference)", desktop: "(min-width: 861px)" },
          (match) => {
            if (!match.conditions?.motion) return;
            const rise = match.conditions.desktop ? 22 : 12;
            const timeline = gsap.timeline({ defaults: { duration: 0.62, ease: "power3.out" } });

            timeline
              .fromTo(".hero-kicker", { autoAlpha: 0, y: 8 }, { autoAlpha: 1, y: 0, clearProps: "transform,opacity,visibility" })
              .fromTo(".headline-line > span", { autoAlpha: 0, yPercent: 115 }, { autoAlpha: 1, yPercent: 0, stagger: 0.09, duration: 0.76, ease: "power4.out", clearProps: "transform,opacity,visibility" }, "-=0.38")
              .fromTo(".hero-copy > p, .page-intro > p", { autoAlpha: 0, y: rise }, { autoAlpha: 1, y: 0, clearProps: "transform,opacity,visibility" }, "-=0.5");

            if (view === "workbench" && runState === "idle") {
              timeline
                .fromTo(".capability-strip > div", { autoAlpha: 0, y: rise, scale: 0.98 }, { autoAlpha: 1, y: 0, scale: 1, stagger: 0.07, clearProps: "transform,opacity,visibility" }, "-=0.4")
                .fromTo(".snapshot-hint", { autoAlpha: 0, y: 12 }, { autoAlpha: 1, y: 0, clearProps: "transform,opacity,visibility" }, "-=0.34")
                .fromTo(".scenario-grid > button", { autoAlpha: 0, y: 16 }, { autoAlpha: 1, y: 0, stagger: 0.055, clearProps: "transform,opacity,visibility" }, "-=0.34")
                .fromTo(".landing .composer-wrap", { autoAlpha: 0, y: 12 }, { autoAlpha: 1, y: 0, clearProps: "transform,opacity,visibility" }, "-=0.32");
            } else if (view === "workbench") {
              timeline
                .fromTo(".question-row", { autoAlpha: 0, y: 12 }, { autoAlpha: 1, y: 0, clearProps: "transform,opacity,visibility" }, "-=0.38")
                .fromTo(".progress-shell, .result-block", { autoAlpha: 0, y: rise, scale: 0.99 }, { autoAlpha: 1, y: 0, scale: 1, clearProps: "transform,opacity,visibility" }, "-=0.34");
            } else if (view === "runs") {
              timeline
                .fromTo(".history-table", { autoAlpha: 0, y: rise }, { autoAlpha: 1, y: 0, clearProps: "transform,opacity,visibility" }, "-=0.38")
                .fromTo(".history-table > button", { autoAlpha: 0, y: 10 }, { autoAlpha: 1, y: 0, stagger: 0.06, clearProps: "transform,opacity,visibility" }, "-=0.35")
                .fromTo(".history-summary > div", { autoAlpha: 0, y: 12 }, { autoAlpha: 1, y: 0, stagger: 0.055, clearProps: "transform,opacity,visibility" }, "-=0.36");
            } else {
              timeline
                .fromTo(".architecture-strip > div", { autoAlpha: 0, y: rise }, { autoAlpha: 1, y: 0, stagger: 0.065, clearProps: "transform,opacity,visibility" }, "-=0.38")
                .fromTo(".engineering-grid > section", { autoAlpha: 0, y: 16 }, { autoAlpha: 1, y: 0, stagger: 0.08, clearProps: "transform,opacity,visibility" }, "-=0.34")
                .fromTo(".eval-proof > div", { autoAlpha: 0, y: 10 }, { autoAlpha: 1, y: 0, stagger: 0.05, clearProps: "transform,opacity,visibility" }, "-=0.34");
            }
          },
        );
        cleanup = () => media.revert();
      }, consoleRef);
      const mediaCleanup = cleanup;
      cleanup = () => { mediaCleanup?.(); context.revert(); };
    });
    return () => { disposed = true; cleanup?.(); };
  }, [view, runState]);

  useEffect(() => {
    let disposed = false;
    let cleanup: (() => void) | undefined;
    void import("gsap").then(({ gsap }) => {
      if (disposed || !consoleRef.current) return;
      const context = gsap.context(() => {
        const media = gsap.matchMedia();
        media.add("(prefers-reduced-motion: no-preference)", () => {
          const items = ".detail-content > .snapshot-banner, .detail-content .panel-summary, .detail-content .trace-list > button, .detail-content .tool-list > button, .detail-content .knowledge-list > button";
          gsap.fromTo(items, { autoAlpha: 0, x: 10 }, { autoAlpha: 1, x: 0, duration: 0.46, stagger: 0.045, ease: "power3.out", clearProps: "transform,opacity,visibility" });
        });
        cleanup = () => media.revert();
      }, consoleRef);
      const mediaCleanup = cleanup;
      cleanup = () => { mediaCleanup?.(); context.revert(); };
    });
    return () => { disposed = true; cleanup?.(); };
  }, [detailTab, scenarioId]);

  const stopTimers = () => { timers.current.forEach(clearTimeout); timers.current = []; };
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setModal(null);
      setApprovalOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      stopTimers();
      window.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  function reset() {
    stopTimers(); setView("workbench"); setRunState("idle"); setStage(0); setQuery("");
    setTicketStatus("idle"); setCheckedSteps([]); setDetailTab("trace"); setRunResponse(null);
    setRunError(null); setRuntimeMode(hasConfiguredApi() ? "configured" : "fixture");
  }

  function selectScenario(item: Scenario) {
    stopTimers(); setScenarioId(item.id); setQuery(item.question); setRunState("idle");
    setStage(0); setTicketStatus("idle"); setCheckedSteps([]); setView("workbench");
    setRunResponse(null); setRunError(null);
  }

  function openCompleted(item: Scenario) {
    stopTimers(); setScenarioId(item.id); setQuery(item.question); setRunState("complete");
    setStage(traceStages.length); setTicketStatus("idle"); setCheckedSteps([]); setView("workbench");
    setRunResponse(null); setRunError(null);
  }

  function scheduleProgress() {
    traceStages.forEach((_, index) => {
      timers.current.push(setTimeout(() => setStage(index + 1), 650 * (index + 1)));
    });
  }

  function completeFixture() {
    stopTimers(); setStage(traceStages.length); setRunState("complete");
  }

  async function startRun() {
    if (!query.trim()) return;
    stopTimers(); setRunState("running"); setStage(0); setTicketStatus("idle"); setDetailTab("trace");
    setRunResponse(null); setRunError(null); scheduleProgress();
    if (!hasConfiguredApi()) {
      timers.current.push(setTimeout(completeFixture, 650 * traceStages.length + 450));
      return;
    }
    try {
      const response = await invokeDiagnosis(query.trim());
      if (response.clarification_question) {
        stopTimers(); setRunState("idle"); setStage(0);
        setModal({
          title: "需要补充信息",
          subtitle: "Agent 拒绝猜测缺失的业务标识",
          body: response.clarification_question,
        });
        return;
      }
      stopTimers(); setRunResponse(response); setRuntimeMode("api");
      setStage(Math.max(response.events.length, traceStages.length)); setRunState("complete");
    } catch (error) {
      setRuntimeMode("fallback");
      setRunError(error instanceof Error ? error.message : "Agent API 暂时不可用");
      timers.current.push(setTimeout(completeFixture, 700));
    }
  }

  async function decideApproval(decision: "approve" | "reject") {
    if (!runResponse || !hasConfiguredApi()) {
      setTicketStatus(decision === "approve" ? "created" : "rejected");
      setApprovalOpen(false);
      return;
    }
    setApprovalPending(true);
    try {
      const response = await resumeDiagnosis(runResponse.run_id, decision);
      setRunResponse(response);
      setTicketStatus(decision === "approve" ? "created" : "rejected");
      setApprovalOpen(false);
    } catch (error) {
      setModal({
        title: "审批操作未完成",
        subtitle: "Agent API 返回错误",
        body: error instanceof Error ? error.message : "请检查后端服务后重试。",
        code: true,
      });
      setApprovalOpen(false);
    } finally {
      setApprovalPending(false);
    }
  }

  function showTool(tool: Scenario["tools"][number]) {
    setModal({ title: tool.name, subtitle: `Mock ERP REST API · read-only · ${tool.latency} ms`, code: true, body: `REQUEST\nPOST /internal/tools/${tool.name}\ncontent-type: application/json\nx-run-id: ${runId}\n\n${prettyJson(tool.request)}\n\nRESPONSE · 200 OK · ${tool.latency} ms\ncontent-type: application/json\n\n${prettyJson(tool.response)}\n\nAUDIT\nside_effect: false\nretry_count: 0\nresult_used_by: evidence_guard` });
  }

  function showSource(source: Scenario["sources"][number]) {
    setModal({ title: source.title, subtitle: `${source.id} · enterprise-kb · relevance ${source.score}%`, body: `文档片段\n${source.excerpt}\n\n检索元数据\nchunk_id: ${source.id}\nretrieval: ${scenario.retrievalLabel ?? "deterministic evidence retrieval"}\nscore: ${source.score / 100}\ncitation_validated: true\n\n该片段来自 synthetic enterprise documentation，仅用于作品集演示。` });
  }

  function showTrace(event: TraceEvent, index: number) {
    setModal({ title: event.label, subtitle: `${event.node} · step ${index + 1}/${getTraceEvents(scenario).length} · ${event.latency} ms`, code: true, body: `NODE\n${event.node}\n\nINPUT\nrun_id: ${runId}\nthread_id: ${runResponse?.thread_id ?? `THREAD-${runId.slice(-6)}`}\nscenario: ${scenario.id}\n\nOUTPUT\n${event.output}\n\nOBSERVABILITY\nstatus: succeeded\nlatency_ms: ${event.latency}\ntrace_level: safe_summary` });
  }

  async function copyText(text: string) {
    await navigator.clipboard?.writeText(text);
    setCopied(true); setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="console" ref={consoleRef}>
      <aside className="app-sidebar" aria-label="主导航">
        <button className="side-brand" onClick={reset} aria-label="返回新建诊断">
          <span className="side-brand-mark"><Sparkles size={22} /></span>
          <span><strong>Support Copilot</strong><small>企业智能运维</small></span>
        </button>
        <button className="new-run" onClick={reset}><Plus size={18} />新建诊断</button>
        <nav>
          <span className="nav-label">工作空间</span>
          {navItems.map(({ id, label, icon: Icon }) => (
            <button key={id} className={view === id ? "active" : ""} onClick={() => setView(id)}>
              <Icon size={17} /><span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="recent-runs">
          <span className="nav-label">最近运行</span>
          {scenarios.slice(0, 3).map((item, index) => (
            <button key={item.id} onClick={() => openCompleted(item)}>
              <i className={`status-color status-${index}`} />
              <span><strong>{item.title}</strong><small>{index === 0 ? "刚刚" : index === 1 ? "12 分钟前" : "今天 09:42"}</small></span>
              <ChevronRight size={14} />
            </button>
          ))}
        </div>
        <div className="service-status"><i /><span><strong>{runtimeMode === "api" ? "Agent API 已连接" : runtimeMode === "fallback" ? "离线回放模式" : runtimeMode === "configured" ? "Agent API 已配置" : "演示快照模式"}</strong><small>Synthetic sandbox</small></span></div>
      </aside>

      <div className="app-stage">
        <header className="app-header">
          <div><strong>{view === "workbench" ? "诊断工作台" : view === "runs" ? "运行记录" : "工程视图"}</strong><small>Expense ERP · Portfolio Demo</small></div>
          <div className="header-badges"><span><i /> {runtimeMode === "api" ? "FULL STACK" : "DEMO 环境"}</span><b>FDE</b></div>
        </header>

        {view === "workbench" && (
          <div className="workbench-grid">
            <main className="workbench-main">
              {runError && <div className="runtime-alert" role="status"><ShieldCheck size={16} /><span><strong>真实后端暂时不可用，已切换到离线演示。</strong><small>{runError}</small></span></div>}
              {runState === "idle" ? (
                <Landing query={query} setQuery={setQuery} onStart={startRun} onSelect={selectScenario} />
              ) : (
                <RunWorkspace
                  scenario={scenario} runId={runId} runState={runState} stage={stage}
                  checkedSteps={checkedSteps} onToggleStep={(index) => setCheckedSteps((prev) => prev.includes(index) ? prev.filter((x) => x !== index) : [...prev, index])}
                  onSource={showSource} ticketStatus={ticketStatus} onApproval={() => setApprovalOpen(true)}
                  query={query} setQuery={setQuery} onStart={startRun}
                />
              )}
            </main>
            <EvidencePanel
              scenario={scenario} runId={runId} runState={runState} stage={stage}
              activeTab={detailTab} setActiveTab={setDetailTab} onTrace={showTrace} onTool={showTool} onSource={showSource}
              onJson={() => setModal({ title: "结构化输出 JSON", subtitle: `${scenario.runtime === "api" ? "Actual FastAPI response" : "Deterministic fixture"} · application/json`, code: true, body: JSON.stringify(runResponse ?? {
                run_id: runId, category: scenario.category, confidence: scenario.confidence / 100,
                selected_tools: scenario.tools.map((tool) => tool.name), retrieved_docs: scenario.sources.map((source) => source.id),
                risk: scenario.risk, escalation_required: scenario.needsApproval, grounded: true,
              }, null, 2) })}
            />
          </div>
        )}
        {view === "runs" && <RunHistory onOpen={openCompleted} />}
        {view === "engineering" && <EngineeringView activeTab={engTab} setActiveTab={setEngTab} onCopy={copyText} copied={copied} />}
      </div>

      <nav className="mobile-nav" aria-label="移动端导航">
        {navItems.map(({ id, label, icon: Icon }) => <button key={id} className={view === id ? "active" : ""} onClick={() => setView(id)}><Icon size={18} /><span>{label}</span></button>)}
      </nav>

      {modal && <DetailModal detail={modal} onClose={() => setModal(null)} onCopy={() => copyText(modal.body)} copied={copied} />}
      {approvalOpen && (
        <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setApprovalOpen(false)}>
          <section className="approval-dialog" role="dialog" aria-modal="true" aria-labelledby="approval-title">
            <span className="approval-icon"><TicketCheck /></span>
            <span className="micro-label">DETERMINISTIC POLICY GATE</span>
            <h2 id="approval-title">确认创建 {scenario.risk === "高风险" ? "P1" : "P2"} 运维工单？</h2>
            <p>这是一次写操作。Graph 已在 <code>create_ticket</code> 前暂停，只有你的明确批准才会继续执行。</p>
            <div className="approval-preview"><span>Action</span><code>create_ticket</code><span>Run</span><code>{runId}</code><span>Policy</span><code>REQUIRE_CONFIRM</code></div>
            <div className="modal-actions">
              <button className="ghost-button" disabled={approvalPending} onClick={() => void decideApproval("reject")}>拒绝，不执行</button>
              <button className="primary-action" disabled={approvalPending} onClick={() => void decideApproval("approve")}><Check size={16} />{approvalPending ? "处理中…" : "确认创建"}</button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

function Landing({ query, setQuery, onStart, onSelect }: { query: string; setQuery: (value: string) => void; onStart: () => void; onSelect: (item: Scenario) => void }) {
  return <div className="landing">
    <div className="hero-copy">
      <span className="hero-kicker"><Sparkles size={15} /> ENTERPRISE SUPPORT COPILOT</span>
      <h1><span className="headline-line"><span>把复杂的系统问题，</span></span><span className="headline-line"><span><em>变成可验证的诊断。</em></span></span></h1>
      <p>描述报销系统中的操作、权限、审批、主数据、凭证或接口问题。Agent 会先补齐上下文，再检索知识并按需查询模拟 ERP。</p>
    </div>
    <div className="capability-strip" aria-label="核心能力">
      <div><span><Layers3 /></span><strong>问题路由</strong><small>6 类故障结构化分类</small></div>
      <div><span><BookOpen /></span><strong>可信检索</strong><small>企业知识库 Top 3 引用</small></div>
      <div><span><ShieldCheck /></span><strong>受控执行</strong><small>写操作强制人工确认</small></div>
    </div>
    <div className="snapshot-hint"><span><Activity /></span><div><strong>右侧已加载一条完整运行快照</strong><p>切换「执行轨迹 / 工具调用 / 知识来源」，每一项都可以点开查看输入、输出和审计信息。</p></div><b>可交互</b></div>
    <section className="scenario-section">
      <div className="section-heading"><strong>试一个真实场景</strong><span>点击填入问题，再由你开始分析</span></div>
      <div className="scenario-grid">
        {scenarios.map((item, index) => <button key={item.id} onClick={() => onSelect(item)}><span className={`scenario-icon tone-${index}`}>{index === 0 ? <FileJson /> : index === 1 ? <Database /> : index === 2 ? <ShieldCheck /> : <Zap />}</span><span><strong>{item.title}</strong><small>{item.claim} · {item.caption}</small></span><ChevronRight /></button>)}
      </div>
    </section>
    <QueryComposer query={query} setQuery={setQuery} onStart={onStart} />
  </div>;
}

function QueryComposer({ query, setQuery, onStart }: { query: string; setQuery: (value: string) => void; onStart: () => void }) {
  return <div className="composer-wrap">
    <label htmlFor="support-query">描述系统问题</label>
    <div className="composer">
      <textarea id="support-query" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="例如：CLM-2026-005 为什么凭证生成失败？" />
      <div><span><ShieldCheck size={13} />只读查询默认安全；写操作需人工确认</span><button disabled={!query.trim()} onClick={onStart}>开始诊断<ArrowUp size={16} /></button></div>
    </div>
    <small className="synthetic-note">本演示仅使用合成数据。Agent 在证据不足时会明确请求补充信息。</small>
  </div>;
}

function RunWorkspace(props: {
  scenario: Scenario; runId: string; runState: "running" | "complete"; stage: number;
  checkedSteps: number[]; onToggleStep: (index: number) => void; onSource: (source: Scenario["sources"][number]) => void;
  ticketStatus: "idle" | "created" | "rejected"; onApproval: () => void; query: string; setQuery: (value: string) => void; onStart: () => void;
}) {
  const { scenario, runId, runState, stage, checkedSteps, onToggleStep, onSource, ticketStatus, onApproval, query, setQuery, onStart } = props;
  return <div className="run-workspace">
    <div className="agent-row"><span><Bot /></span><div><strong>Support Agent</strong><small>RAG · Tool Calling · Human-in-the-loop</small></div></div>
    <div className="question-row"><b>你</b><div><span>你的问题</span><p>{query}</p></div></div>
    {runState === "running" ? <ProgressCard stage={stage} /> : (
      <div className="result-block">
        <div className="result-author"><span><Sparkles /></span><strong>Support Copilot · 诊断完成</strong><button>{runId}</button></div>
        <article className="diagnosis-card">
          <div className="diagnosis-hero"><div><span className="micro-label">根因判断</span><h2>{scenario.rootCause}</h2></div><span className={`risk-pill ${scenario.risk}`}>{scenario.risk}</span></div>
          <div className="metric-row"><div><span>问题分类</span><strong>{scenario.category}</strong></div><div><span>证据置信度</span><strong>{scenario.confidence}%</strong></div><div><span>运行耗时</span><strong>{scenario.duration}</strong></div></div>
          <section className="diagnosis-section"><div className="subheading"><strong>诊断证据</strong><span>工具结果与知识交叉验证</span></div>{scenario.sources[0] ? <button className="evidence-proof" onClick={() => onSource(scenario.sources[0])}><Check size={16} /><span>{scenario.evidence}</span><ChevronRight size={15} /></button> : <div className="evidence-proof"><ShieldCheck size={16} /><span>{scenario.evidence}</span></div>}</section>
          <section className="diagnosis-section"><div className="subheading"><strong>建议处理步骤</strong><span>{checkedSteps.length}/{scenario.steps.length} 已完成</span></div><div className="step-list">{scenario.steps.map((step, index) => <button className={checkedSteps.includes(index) ? "done" : ""} key={step} onClick={() => onToggleStep(index)}><span>{checkedSteps.includes(index) ? <Check size={14} /> : index + 1}</span><strong>{step}</strong></button>)}</div></section>
          <section className="diagnosis-section"><div className="subheading"><strong>引用知识</strong><span>{scenario.retrievalLabel ?? "Deterministic retrieval"}</span></div><div className="source-cards">{scenario.sources.map((source) => <button key={source.id} onClick={() => onSource(source)}><span>{source.id}</span><strong>{source.title}</strong><small>{source.score}%</small></button>)}</div></section>
          {scenario.needsApproval && ticketStatus === "idle" && <div className="escalation-card"><span><TicketCheck /></span><div><strong>建议升级人工支持</strong><p>涉及受控配置或高风险故障，创建工单需要人工确认。</p></div><button onClick={onApproval}>创建工单</button></div>}
          {ticketStatus !== "idle" && <div className={`ticket-result ${ticketStatus}`}><span>{ticketStatus === "created" ? <Check /> : <X />}</span><div><strong>{ticketStatus === "created" ? "工单已创建" : "已拒绝写操作"}</strong><p>{ticketStatus === "created" ? `${scenario.ticketId ?? "INC-2481"} · 已使用 run_id 作为幂等键。` : "Graph 已结束，Mock ERP 未收到写入请求。"}</p></div></div>}
        </article>
      </div>
    )}
    <QueryComposer query={query} setQuery={setQuery} onStart={onStart} />
  </div>;
}

function ProgressCard({ stage }: { stage: number }) {
  const percent = Math.min(100, Math.max(8, stage * 20));
  return <div className="progress-shell"><div className="result-author"><span><Sparkles /></span><strong>Support Copilot · 正在分析</strong></div><div className="progress-card"><div className="progress-head"><span className="spinner" /><div><strong>{traceStages[Math.min(stage, 4)][0]}</strong><small>{traceStages[Math.min(stage, 4)][1]}</small></div><b>{percent}%</b></div><div className="progress-bar"><i style={{ width: `${percent}%` }} /></div><div className="progress-stages">{traceStages.map(([label], index) => <div className={index < stage ? "done" : index === stage ? "active" : ""} key={label}><span>{index < stage ? <Check size={13} /> : index + 1}</span><small>{label}</small></div>)}</div></div></div>;
}

function EvidencePanel(props: {
  scenario: Scenario; runId: string; runState: "idle" | "running" | "complete"; stage: number;
  activeTab: DetailTab; setActiveTab: (tab: DetailTab) => void; onTrace: (event: TraceEvent, index: number) => void;
  onTool: (tool: Scenario["tools"][number]) => void;
  onSource: (source: Scenario["sources"][number]) => void; onJson: () => void;
}) {
  const { scenario, runId, runState, stage, activeTab, setActiveTab, onTrace, onTool, onSource, onJson } = props;
  const events = getTraceEvents(scenario);
  const isSnapshot = runState === "idle";
  const isComplete = runState === "complete" || isSnapshot;
  const tabMeta: Record<DetailTab, { label: string; count: number }> = {
    trace: { label: "执行轨迹", count: events.length },
    tools: { label: "工具调用", count: scenario.tools.length },
    knowledge: { label: "知识来源", count: scenario.sources.length },
  };
  return <aside className="evidence-panel" aria-label="Agent 执行详情">
    <div className="evidence-header"><div><strong>执行详情</strong><small>{runId} · {scenario.claim}</small></div><span className={isComplete ? "complete" : "running"}>{isSnapshot ? <><CircleDot size={12} />示例快照</> : runState === "complete" ? <><Check size={12} />完成</> : <><Activity size={12} />执行中</>}</span></div>
    <div className="detail-tabs" role="tablist">{(["trace", "tools", "knowledge"] as DetailTab[]).map((tab) => <button role="tab" aria-selected={activeTab === tab} className={activeTab === tab ? "active" : ""} key={tab} onClick={() => setActiveTab(tab)}><span>{tabMeta[tab].label}</span><b>{tabMeta[tab].count}</b></button>)}</div>
    <div className="detail-content">
      {isSnapshot && <div className="snapshot-banner"><Sparkles /><p><strong>作品演示快照</strong>当前内容来自最近一次脱敏运行，可直接点击查看；发起诊断后会切换为实时推进。</p></div>}
      {activeTab === "trace" ? (
        <div className="trace-list">{events.map((event, index) => {
          const done = isComplete || index < stage;
          const active = runState === "running" && index === stage;
          return <button className={done ? "done" : active ? "active" : "queued"} key={event.node} disabled={!done && !active} onClick={() => onTrace(event, index)}><span>{done ? <Check size={13} /> : index + 1}</span><div><strong>{event.label}<code>{event.node}</code></strong><small>{event.caption}</small></div><b>{done ? `${event.latency} ms` : active ? "RUNNING" : "QUEUED"}</b><ChevronRight /></button>;
        })}</div>
      ) : activeTab === "tools" ? (
        <div className="tool-list"><div className="panel-summary"><span>REST boundary</span><strong>{scenario.tools.length} 次只读调用</strong><small>0 retry · 0 side effect</small></div>{scenario.tools.map((tool) => { const available = isComplete || stage >= 4; return <button key={tool.name} disabled={!available} onClick={() => onTool(tool)}><span><Wrench /></span><div><strong>{tool.name}</strong><small>{available ? `200 OK · ${tool.latency} ms · READ ONLY` : "等待 execute_tools 节点"}</small></div><i className={available ? "ok" : ""}>{available ? "OK" : "—"}</i><ChevronRight /></button>; })}</div>
      ) : (
        <div className="knowledge-list"><div className="panel-summary"><span>{scenario.retrievalLabel ?? "Deterministic retrieval"}</span><strong>Top {scenario.sources.length} 已通过引用校验</strong><small>collection: enterprise-kb</small></div>{scenario.sources.map((source) => { const available = isComplete || stage >= 2; return <button key={source.id} disabled={!available} onClick={() => onSource(source)}><span><BookOpen /></span><div><strong>{source.title}</strong><small>{source.id} · score {source.score / 100}</small><p>{source.excerpt}</p></div><i>{source.score}%</i><ChevronRight /></button>; })}</div>
      )}
    </div>
    <div className="evidence-footer"><button onClick={onJson} disabled={!isComplete}><span><Braces /></span><div><strong>结构化输出</strong><small>{isSnapshot ? "查看该快照的 API JSON" : "查看 API JSON 响应"}</small></div><ChevronRight /></button><div className="eval-mini"><span><strong>54</strong><small>Eval cases</small></span><span><strong>100%</strong><small>Retrieval hit@3</small></span></div><p>deterministic baseline · synthetic data · rerunnable</p></div>
  </aside>;
}

function RunHistory({ onOpen }: { onOpen: (item: Scenario) => void }) {
  return <main className="page-view"><div className="page-intro"><span className="hero-kicker"><History size={15} /> AUDITABLE RUNS</span><h1><span className="headline-line"><span>每一次判断，</span></span><span className="headline-line"><span>都能沿证据链复盘。</span></span></h1><p>运行记录保留问题分类、检索来源、工具结果、人工决策和最终状态。这里展示的是脱敏的合成运行。</p></div><div className="history-table"><div className="history-head"><span>运行</span><span>分类</span><span>风险</span><span>状态</span><span>耗时</span><span /></div>{scenarios.map((item) => <button key={item.id} onClick={() => onOpen(item)}><span><b>{getRunId(item.id)}</b><small>{item.question}</small></span><span>{item.category}</span><span><i className={`risk-dot ${item.risk}`} />{item.risk}</span><span className="success-state"><Check size={15} />完成</span><span>{item.duration}</span><ChevronRight size={17} /></button>)}</div><div className="history-summary"><div><strong>54</strong><span>评测案例</span></div><div><strong>0</strong><span>基线执行失败</span></div><div><strong>100%</strong><span>Citation coverage</span></div><div><strong>100%</strong><span>Retrieval hit@3</span></div></div><p className="baseline-disclaimer">这些指标来自仓库内 deterministic baseline 的实际结果，不代表生产模型准确率。</p></main>;
}

const codeSnapshots = {
  code: `def approval(state: AgentState):\n    decision = interrupt({\n        "action": "create_ticket",\n        "policy": "REQUIRE_CONFIRM",\n        "run_id": state["run_id"],\n    })\n    return {"approval": decision}\n\n# Side effect occurs only after resume + approve`,
  json: `{\n  "run_id": "RUN-8F21A4",\n  "category": "凭证 / 配置问题",\n  "selected_tools": [\n    "get_claim_status",\n    "get_voucher_status"\n  ],\n  "citations": ["KB-008", "KB-009", "KB-012"],\n  "grounded": true\n}`,
  trace: `RUN-8F21A4\n├─ analyze ............ 42 ms\n├─ retrieve ......... 128 ms\n├─ plan_tools ......... 18 ms\n├─ execute_tools ..... 244 ms\n├─ evidence_guard ..... PASS\n└─ diagnose .......... 612 ms`,
};

function EngineeringView({ activeTab, setActiveTab, onCopy, copied }: { activeTab: EngineeringTab; setActiveTab: (tab: EngineeringTab) => void; onCopy: (text: string) => void; copied: boolean }) {
  return <main className="page-view engineering"><div className="page-intro"><span className="hero-kicker"><Code2 size={15} /> ENGINEERING VIEW</span><h1><span className="headline-line"><span>不是一个聊天框，</span></span><span className="headline-line"><span>是一条可测试的交付链路。</span></span></h1><p>从浏览器到 Agent API、LangGraph、RAG、Mock ERP 与 Eval，每一层都有清晰职责和可验证边界。</p></div>
    <section className="architecture-strip"><div><Home /><strong>React Workbench</strong><small>REST / JSON</small></div><ChevronRight /><div><Bot /><strong>FastAPI Agent</strong><small>LangGraph</small></div><ChevronRight /><div><BookOpen /><strong>RAG + Chroma</strong><small>Top 3 evidence</small></div><ChevronRight /><div><Database /><strong>Mock ERP API</strong><small>Synthetic SQLite</small></div></section>
    <div className="engineering-grid"><section className="code-panel"><div className="code-tabs">{(["code", "json", "trace"] as EngineeringTab[]).map((tab) => <button className={activeTab === tab ? "active" : ""} key={tab} onClick={() => setActiveTab(tab)}>{tab === "code" ? <><Code2 />Code</> : tab === "json" ? <><FileJson />JSON</> : <><Terminal />Trace</>}</button>)}<button className="copy-button" onClick={() => onCopy(codeSnapshots[activeTab])}>{copied ? <Check /> : <Copy />}{copied ? "已复制" : "复制"}</button></div><div className="code-caption"><span>示例 / 运行快照</span><small>已脱敏，不含模型私有推理或环境变量</small></div><pre><code>{codeSnapshots[activeTab]}</code></pre></section>
      <section className="principles-panel"><span className="micro-label">设计原理 / 面试看点</span><div><span><ShieldCheck /></span><strong>为什么 Agent 不直连 ERP 数据库？</strong><p>REST 边界保留系统所有权、JSON 契约、鉴权位置和完整审计轨迹。</p></div><div><span><TicketCheck /></span><strong>为什么写操作必须 HITL？</strong><p>LLM 只能提议；确定性策略在 side effect 之前中断并等待责任人批准。</p></div><div><span><CircleDot /></span><strong>证据门如何防幻觉？</strong><p>输出引用必须属于当次 Top 3；无有效工具证据时会降低置信度并明确不足。</p></div><div><span><Activity /></span><strong>run_id 与 thread_id</strong><p>run_id 标识一次诊断与幂等写入；thread_id 标识可暂停、可恢复的 Graph checkpoint。</p></div></section>
    </div>
    <section className="eval-proof"><div><span className="micro-label">ACTUAL BASELINE</span><h2>评测结果来自仓库内实际 runner</h2><p>54 条人工 ground truth · deterministic-baseline-v2 · 0 execution failures</p></div><div><strong>100%</strong><small>Classification</small></div><div><strong>100%</strong><small>Tool selection</small></div><div><strong>100%</strong><small>Retrieval hit@3</small></div><div><strong>100%</strong><small>Evidence validity</small></div></section>
  </main>;
}

function DetailModal({ detail, onClose, onCopy, copied }: { detail: { title: string; subtitle: string; body: string; code?: boolean }; onClose: () => void; onCopy: () => void; copied: boolean }) {
  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><section className="detail-modal" role="dialog" aria-modal="true" aria-labelledby="detail-title"><div className="detail-modal-head"><div><span className="micro-label">TRACE DETAIL</span><h2 id="detail-title">{detail.title}</h2><p>{detail.subtitle}</p></div><button aria-label="关闭详情" onClick={onClose}><X /></button></div>{detail.code ? <pre><code>{detail.body}</code></pre> : <div className="source-excerpt">{detail.body}</div>}<div className="modal-explainer"><strong>为什么展示这个？</strong><p>面试时可以沿着这条记录解释 Agent 如何从输入、检索和工具结果形成最终结论。</p></div><div className="modal-actions"><button className="ghost-button" onClick={onCopy}>{copied ? <Check size={15} /> : <Clipboard size={15} />}{copied ? "已复制" : "复制内容"}</button><button className="primary-action" onClick={onClose}>完成</button></div></section></div>;
}
