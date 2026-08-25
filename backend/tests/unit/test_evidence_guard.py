from services.agent_api.app.agent.evidence_guard import validate_diagnosis
from services.agent_api.app.agent.state import Citation, Diagnosis, Evidence


def test_guard_removes_hallucinated_citation_and_lowers_confidence():
    diagnosis = Diagnosis(
        category="operation",
        category_label="操作问题",
        possible_causes=["未知"],
        evidence=[],
        citations=[Citation(doc_id="FAKE", chunk_id="FAKE#C01", title="不存在", section="假")],
        troubleshooting_steps=["补充信息"],
        risk_level="low",
        escalation_required=False,
        confidence=0.95,
    )
    guarded = validate_diagnosis(diagnosis, [], [])
    assert guarded.citations == []
    assert guarded.confidence <= 0.5
    assert guarded.uncertainty_statement


def test_guard_removes_evidence_that_does_not_reference_this_run():
    diagnosis = Diagnosis(
        category="permission",
        category_label="权限问题",
        possible_causes=["权限缺失"],
        evidence=[
            Evidence(
                evidence_id="E-01",
                source_type="tool",
                source_id="TOOL-made-up",
                statement="一个不属于本次运行的工具结论",
            )
        ],
        citations=[],
        troubleshooting_steps=["补充信息"],
        risk_level="medium",
        escalation_required=True,
        confidence=0.95,
    )
    guarded = validate_diagnosis(
        diagnosis,
        [],
        [
            {
                "evidence_id": "TOOL-get_user_permissions",
                "tool_name": "get_user_permissions",
                "ok": True,
                "result": {"missing": ["expense.travel.submit"]},
            }
        ],
    )
    assert guarded.evidence == []
    assert guarded.confidence <= 0.5
    assert guarded.uncertainty_statement
