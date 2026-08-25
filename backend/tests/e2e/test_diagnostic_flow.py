from services.agent_api.app.agent.evidence_guard import validate_diagnosis
from services.agent_api.app.agent.model_gateway import ModelGateway
from services.agent_api.app.core.config import Settings
from services.agent_api.app.observability.events import RunRepository
from services.agent_api.app.rag.retriever import KnowledgeRetriever
from services.agent_api.app.tools.erp_client import SyntheticFixtureERPClient
from services.agent_api.app.tools.executor import AuditedToolExecutor


def test_offline_diagnostic_flow_has_grounded_answer(tmp_path):
    settings = Settings(llm_provider="deterministic")
    model = ModelGateway(settings)
    issue = model.analyze("CLM-2026-007 附件同步接口为什么失败？")
    chunks = KnowledgeRetriever(settings).search(issue.summary, issue.category)
    runs = RunRepository(tmp_path / "runs.db")
    runs.start_run("run-e2e", "thread-e2e", issue.summary)
    executor = AuditedToolExecutor(SyntheticFixtureERPClient(), runs)
    results = [
        executor.execute("run-e2e", call) for call in model.choose_tools(issue.summary, issue)
    ]
    diagnosis = validate_diagnosis(
        model.diagnose(issue.summary, issue, chunks, results), chunks, results
    )
    assert diagnosis.category == "interface_system"
    assert diagnosis.risk_level == "high"
    assert diagnosis.escalation_required is True
    assert any(item.doc_id == "KB-010" for item in diagnosis.citations)
    assert diagnosis.evidence
