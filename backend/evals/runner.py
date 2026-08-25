from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from services.agent_api.app.agent.evidence_guard import validate_diagnosis
from services.agent_api.app.agent.model_gateway import ModelGateway
from services.agent_api.app.core.config import Settings
from services.agent_api.app.observability.events import RunRepository
from services.agent_api.app.rag.retriever import KnowledgeRetriever
from services.agent_api.app.tools.erp_client import SyntheticFixtureERPClient
from services.agent_api.app.tools.executor import AuditedToolExecutor

from .metrics import aggregate, exact_match, retrieval_hit_at_3, set_exact_match
from .report import timestamp, write_report


def load_cases(path: Path) -> list[dict]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def evaluate_case(case: dict, settings: Settings, executor: AuditedToolExecutor) -> dict:
    model = ModelGateway(settings)
    retriever = KnowledgeRetriever(settings)
    issue = model.analyze(case["question"])
    if issue.missing_fields:
        calls, chunks, diagnosis = [], [], None
    else:
        chunks = retriever.search(case["question"], issue.category, k=3)
        calls = model.choose_tools(case["question"], issue)
        tool_results = [executor.execute(case["case_id"], call) for call in calls]
        diagnosis = validate_diagnosis(
            model.diagnose(case["question"], issue, chunks, tool_results), chunks, tool_results
        )
    predicted_tools = [call["name"] for call in calls]
    predicted_docs = [chunk["doc_id"] for chunk in chunks]
    predicted_escalation = diagnosis.escalation_required if diagnosis else False
    valid_citations = 0
    citation_total = 0
    if diagnosis:
        available = {chunk["chunk_id"] for chunk in chunks}
        citation_total = len(diagnosis.citations)
        valid_citations = sum(item.chunk_id in available for item in diagnosis.citations)
    citation_coverage = valid_citations / citation_total if citation_total else float(not chunks)
    evidence_reference_validity = 1.0
    if diagnosis and diagnosis.evidence:
        valid_source_ids = {chunk["chunk_id"] for chunk in chunks} | {
            row["evidence_id"] for row in tool_results if row.get("ok")
        }
        evidence_reference_validity = sum(
            item.source_id in valid_source_ids for item in diagnosis.evidence
        ) / len(diagnosis.evidence)
    return {
        "case_id": case["case_id"],
        "expected": case,
        "predicted": {
            "category": issue.category,
            "tools": predicted_tools,
            "docs": predicted_docs,
            "escalation": predicted_escalation,
        },
        "classification_accuracy": exact_match(case["expected_category"], issue.category),
        "tool_selection_accuracy": set_exact_match(case["expected_tools"], predicted_tools),
        "retrieval_hit_at_3": retrieval_hit_at_3(case["expected_docs"], predicted_docs),
        "escalation_accuracy": exact_match(case["expected_escalation"], predicted_escalation),
        "citation_coverage": citation_coverage,
        "evidence_reference_validity": evidence_reference_validity,
    }


def run(cases_path: Path, output_dir: Path, settings: Settings) -> dict:
    cases = load_cases(cases_path)
    failures = []
    rows = []
    with tempfile.TemporaryDirectory() as temp_dir:
        runs = RunRepository(Path(temp_dir) / "eval.db")
        executor = AuditedToolExecutor(SyntheticFixtureERPClient(), runs)
        for case in cases:
            runs.start_run(case["case_id"], case["case_id"], case["question"])
            try:
                rows.append(evaluate_case(case, settings, executor))
            except Exception as exc:  # failures remain visible and count as zero
                failures.append({"case_id": case["case_id"], "error": repr(exc)})
                rows.append(
                    {
                        "case_id": case["case_id"],
                        **{
                            name: 0.0
                            for name in (
                                "classification_accuracy",
                                "tool_selection_accuracy",
                                "retrieval_hit_at_3",
                                "escalation_accuracy",
                                "citation_coverage",
                                "evidence_reference_validity",
                            )
                        },
                    }
                )
    result = {
        "generated_at": timestamp(),
        "provider": settings.llm_provider,
        "model": settings.llm_model
        if settings.llm_provider != "deterministic"
        else "deterministic-baseline-v2",
        "case_count": len(cases),
        "failed_executions": len(failures),
        "metrics": aggregate(rows),
        "failures": failures,
        "cases": rows,
    }
    write_report(result, output_dir)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=Path("evals/cases.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("evals/results"))
    args = parser.parse_args()
    settings = Settings()
    result = run(args.cases, args.output, settings)
    print(json.dumps(result["metrics"], indent=2))
