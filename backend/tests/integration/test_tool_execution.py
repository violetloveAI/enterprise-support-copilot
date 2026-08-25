from services.agent_api.app.observability.events import RunRepository
from services.agent_api.app.tools.erp_client import SyntheticFixtureERPClient
from services.agent_api.app.tools.executor import AuditedToolExecutor


def test_tool_execution_is_audited(tmp_path):
    runs = RunRepository(tmp_path / "runs.db")
    runs.start_run("run-1", "thread-1", "query")
    executor = AuditedToolExecutor(SyntheticFixtureERPClient(), runs)
    result = executor.execute(
        "run-1", {"name": "get_voucher_status", "args": {"claim_id": "CLM-2026-005"}}
    )
    assert result["ok"] is True
    assert result["result"]["error_code"] == "FI_PERIOD_CLOSED"
    assert runs.events("run-1")[0]["event_type"] == "tool_result"


def test_executor_rejects_write_tool_without_hitl(tmp_path):
    runs = RunRepository(tmp_path / "runs.db")
    result = AuditedToolExecutor(SyntheticFixtureERPClient(), runs).execute(
        "run-2", {"name": "create_ticket", "args": {"summary": "unsafe"}}
    )
    assert result["ok"] is False
