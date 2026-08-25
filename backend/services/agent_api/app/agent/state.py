from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

Category = Literal[
    "operation", "permission", "approval", "master_data", "voucher_config", "interface_system"
]
RiskLevel = Literal["low", "medium", "high"]


class StructuredIssue(BaseModel):
    summary: str
    category: Category
    claim_id: str | None = None
    user_id: str | None = None
    error_code: str | None = None
    interface_name: str | None = None
    missing_fields: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    evidence_id: str
    source_type: Literal["knowledge", "tool"]
    source_id: str
    statement: str


class Citation(BaseModel):
    doc_id: str
    chunk_id: str
    title: str
    section: str


class Diagnosis(BaseModel):
    category: Category
    category_label: str
    possible_causes: list[str]
    evidence: list[Evidence]
    citations: list[Citation]
    troubleshooting_steps: list[str]
    risk_level: RiskLevel
    escalation_required: bool
    escalation_reason: str | None = None
    confidence: float = Field(ge=0, le=1)
    uncertainty_statement: str | None = None


class AgentState(TypedDict, total=False):
    messages: Annotated[list[Any], add_messages]
    run_id: str
    thread_id: str
    user_query: str
    structured_issue: dict[str, Any]
    category: Category
    missing_fields: list[str]
    clarification_question: str | None
    retrieved_chunks: list[dict[str, Any]]
    planned_tools: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    tool_iteration_count: int
    diagnosis: dict[str, Any]
    pending_action: dict[str, Any] | None
    approval_result: str | None
    ticket_result: dict[str, Any] | None
    status: str
    errors: list[str]
