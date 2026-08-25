export type ApiSource = {
  content: string;
  score: number;
  doc_id: string;
  chunk_id: string;
  title: string;
  section: string;
};

export type ApiToolCall = {
  evidence_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  ok: boolean;
  result?: Record<string, unknown>;
  error?: string;
};

export type ApiEvent = {
  sequence: number;
  event_type: string;
  node_name: string;
  status: string;
  duration_ms: number | null;
  details: Record<string, unknown>;
};

export type ApiDiagnosis = {
  category: string;
  category_label: string;
  possible_causes: string[];
  evidence: Array<{
    evidence_id: string;
    source_type: "knowledge" | "tool";
    source_id: string;
    statement: string;
  }>;
  citations: Array<{
    doc_id: string;
    chunk_id: string;
    title: string;
    section: string;
  }>;
  troubleshooting_steps: string[];
  risk_level: "low" | "medium" | "high";
  escalation_required: boolean;
  escalation_reason?: string | null;
  confidence: number;
  uncertainty_statement?: string | null;
};

export type ApiRunResponse = {
  run_id: string;
  thread_id: string;
  status: string;
  clarification_question?: string | null;
  diagnosis?: ApiDiagnosis | null;
  pending_approval?: Record<string, unknown> | null;
  ticket?: Record<string, unknown> | null;
  retrieved_sources: ApiSource[];
  tool_calls: ApiToolCall[];
  events: ApiEvent[];
  llm_provider: string;
  retrieval_provider: string;
};

const configuredBaseUrl = process.env.NEXT_PUBLIC_AGENT_API_URL?.replace(/\/$/, "") ?? "";

export function hasConfiguredApi() {
  return Boolean(configuredBaseUrl);
}

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${configuredBaseUrl}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...init.headers },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload && typeof payload.detail === "string" ? payload.detail : response.statusText;
    throw new Error(`Agent API ${response.status}: ${detail}`);
  }
  return response.json() as Promise<T>;
}

export function invokeDiagnosis(message: string) {
  return request<ApiRunResponse>("/api/v1/chat/invoke", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function resumeDiagnosis(runId: string, decision: "approve" | "reject") {
  return request<ApiRunResponse>(`/api/v1/runs/${encodeURIComponent(runId)}/resume`, {
    method: "POST",
    body: JSON.stringify({ decision }),
  });
}
