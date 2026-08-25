from __future__ import annotations

import time
from typing import Any

from langgraph.types import interrupt

from ..observability.events import RunRepository
from ..rag.retriever import KnowledgeRetriever
from ..tools.erp_client import ERPClientProtocol
from ..tools.executor import AuditedToolExecutor
from .evidence_guard import validate_diagnosis
from .model_gateway import ModelGateway
from .state import AgentState, StructuredIssue


class AgentNodes:
    def __init__(
        self,
        model: ModelGateway,
        retriever: KnowledgeRetriever,
        executor: AuditedToolExecutor,
        erp_client: ERPClientProtocol,
        runs: RunRepository,
    ):
        self.model = model
        self.retriever = retriever
        self.executor = executor
        self.erp_client = erp_client
        self.runs = runs

    def analyze(self, state: AgentState) -> dict[str, Any]:
        started = time.perf_counter()
        issue = self.model.analyze(state["user_query"])
        self.runs.event(
            state["run_id"],
            "classification",
            "analyze",
            duration_ms=int((time.perf_counter() - started) * 1000),
            category=issue.category,
            entities={"claim_id": issue.claim_id, "user_id": issue.user_id},
            missing_fields=issue.missing_fields,
        )
        return {
            "structured_issue": issue.model_dump(),
            "category": issue.category,
            "missing_fields": issue.missing_fields,
            "tool_iteration_count": 0,
            "tool_results": [],
        }

    def clarify(self, state: AgentState) -> dict[str, Any]:
        labels = {
            "user_id": "用户编号（例如 U1002）",
            "claim_id": "报销单号（例如 CLM-2026-003）",
            "user_id_or_claim_id": "用户编号或报销单号",
        }
        names = "、".join(labels.get(item, item) for item in state["missing_fields"])
        question = f"为了继续诊断，请补充{names}。我不会猜测缺失的业务标识。"
        self.runs.event(
            state["run_id"],
            "clarification_required",
            "clarify",
            missing_fields=state["missing_fields"],
        )
        return {"clarification_question": question, "status": "needs_clarification"}

    def retrieve(self, state: AgentState) -> dict[str, Any]:
        started = time.perf_counter()
        chunks = self.retriever.search(state["user_query"], state["category"])
        self.runs.event(
            state["run_id"],
            "retrieval",
            "retrieve",
            duration_ms=int((time.perf_counter() - started) * 1000),
            source_ids=[row["chunk_id"] for row in chunks],
            scores=[round(row["score"], 4) for row in chunks],
        )
        return {"retrieved_chunks": chunks}

    def plan_tools(self, state: AgentState) -> dict[str, Any]:
        issue = StructuredIssue.model_validate(state["structured_issue"])
        calls = self.model.choose_tools(state["user_query"], issue)
        self.runs.event(
            state["run_id"],
            "tool_plan",
            "plan_tools",
            tool_names=[call["name"] for call in calls],
            arguments=[call.get("args", {}) for call in calls],
        )
        return {"planned_tools": calls}

    def execute_tools(self, state: AgentState) -> dict[str, Any]:
        results = [self.executor.execute(state["run_id"], call) for call in state["planned_tools"]]
        return {
            "tool_results": results,
            "tool_iteration_count": state.get("tool_iteration_count", 0) + 1,
        }

    def diagnose(self, state: AgentState) -> dict[str, Any]:
        started = time.perf_counter()
        issue = StructuredIssue.model_validate(state["structured_issue"])
        diagnosis = self.model.diagnose(
            state["user_query"], issue, state["retrieved_chunks"], state["tool_results"]
        )
        diagnosis = validate_diagnosis(diagnosis, state["retrieved_chunks"], state["tool_results"])
        pending_action = None
        if diagnosis.escalation_required:
            pending_action = {
                "name": "create_ticket",
                "args": {
                    "run_id": state["run_id"],
                    "summary": issue.summary,
                    "category": issue.category,
                    "risk_level": diagnosis.risk_level,
                    "claim_id": issue.claim_id,
                    "user_id": issue.user_id,
                    "evidence": [item.statement[:240] for item in diagnosis.evidence],
                },
            }
        self.runs.event(
            state["run_id"],
            "diagnosis",
            "diagnose",
            duration_ms=int((time.perf_counter() - started) * 1000),
            risk_level=diagnosis.risk_level,
            escalation_required=diagnosis.escalation_required,
            confidence=diagnosis.confidence,
            citation_ids=[item.chunk_id for item in diagnosis.citations],
        )
        return {
            "diagnosis": diagnosis.model_dump(),
            "pending_action": pending_action,
            "status": "awaiting_approval" if pending_action else "completed",
        }

    def approval(self, state: AgentState) -> dict[str, Any]:
        action = state["pending_action"]
        decision = interrupt(
            {
                "kind": "tool_approval",
                "message": "诊断建议升级人工。是否批准创建支持工单？",
                "action": action,
                "allowed_decisions": ["approve", "reject"],
            }
        )
        approved = decision is True or (
            isinstance(decision, dict) and decision.get("decision") == "approve"
        )
        if not approved:
            self.runs.event(state["run_id"], "human_decision", "approval", decision="reject")
            return {"approval_result": "rejected", "pending_action": None, "status": "completed"}
        result = self.erp_client.call("create_ticket", action["args"])
        self.runs.event(
            state["run_id"],
            "human_decision",
            "approval",
            decision="approve",
            ticket_id=result.get("ticket_id"),
        )
        return {
            "approval_result": "approved",
            "ticket_result": result,
            "pending_action": None,
            "status": "completed",
        }

    def complete(self, state: AgentState) -> dict[str, Any]:
        return {"status": "completed"}
