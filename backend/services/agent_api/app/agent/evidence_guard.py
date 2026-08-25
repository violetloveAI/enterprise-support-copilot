from __future__ import annotations

from .state import Diagnosis


def validate_diagnosis(
    diagnosis: Diagnosis,
    chunks: list[dict],
    tool_results: list[dict],
) -> Diagnosis:
    allowed_chunks = {row["chunk_id"] for row in chunks}
    allowed_tool_evidence = {
        row["evidence_id"] for row in tool_results if row.get("ok") and row.get("evidence_id")
    }
    diagnosis.citations = [
        citation for citation in diagnosis.citations if citation.chunk_id in allowed_chunks
    ]
    diagnosis.evidence = [
        item
        for item in diagnosis.evidence
        if (
            item.source_type == "tool"
            and item.source_id in allowed_tool_evidence
        )
        or (
            item.source_type == "knowledge"
            and item.source_id in allowed_chunks
        )
    ]
    if not any(row.get("ok") for row in tool_results):
        diagnosis.confidence = min(diagnosis.confidence, 0.55)
        diagnosis.uncertainty_statement = diagnosis.uncertainty_statement or (
            "没有成功的 ERP 工具查询，无法确认具体系统根因。"
        )
    if not diagnosis.citations:
        diagnosis.confidence = min(diagnosis.confidence, 0.5)
        diagnosis.uncertainty_statement = diagnosis.uncertainty_statement or (
            "未检索到可引用的知识依据。"
        )
    if any(row.get("ok") for row in tool_results) and not diagnosis.evidence:
        diagnosis.confidence = min(diagnosis.confidence, 0.6)
        diagnosis.uncertainty_statement = diagnosis.uncertainty_statement or (
            "工具查询成功，但最终答案没有提供可验证的工具证据引用。"
        )
    if diagnosis.risk_level == "high":
        diagnosis.escalation_required = True
        diagnosis.escalation_reason = diagnosis.escalation_reason or "高风险问题必须升级人工。"
    return diagnosis
