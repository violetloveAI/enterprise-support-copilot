from langgraph.types import Command

from services.agent_api.app.agent.graph import build_graph
from services.agent_api.app.core.config import Settings
from services.agent_api.app.tools.erp_client import SyntheticFixtureERPClient


def test_ticket_write_pauses_and_can_be_rejected(tmp_path):
    settings = Settings(
        llm_provider="deterministic",
        copilot_db_path=tmp_path / "copilot.db",
        chroma_path=tmp_path / "chroma",
    )
    graph, runs = build_graph(settings, erp_client=SyntheticFixtureERPClient())
    run_id, thread_id = "run-hitl-0001", "thread-hitl-0001"
    runs.start_run(run_id, thread_id, "CLM-2026-005 凭证失败")
    result = graph.invoke(
        {
            "run_id": run_id,
            "thread_id": thread_id,
            "user_query": "CLM-2026-005 为什么凭证生成失败？",
            "messages": [{"role": "user", "content": "CLM-2026-005 为什么凭证生成失败？"}],
        },
        {"configurable": {"thread_id": thread_id}},
    )
    assert result["__interrupt__"]
    resumed = graph.invoke(
        Command(resume={"decision": "reject"}),
        {"configurable": {"thread_id": thread_id}},
    )
    assert resumed["approval_result"] == "rejected"
    assert resumed.get("ticket_result") is None


def test_ticket_write_executes_once_after_approval(tmp_path):
    settings = Settings(
        llm_provider="deterministic",
        copilot_db_path=tmp_path / "copilot.db",
        chroma_path=tmp_path / "chroma",
    )
    client = SyntheticFixtureERPClient()
    graph, runs = build_graph(settings, erp_client=client)
    run_id, thread_id = "run-hitl-0002", "thread-hitl-0002"
    runs.start_run(run_id, thread_id, "CLM-2026-005 凭证失败")
    result = graph.invoke(
        {
            "run_id": run_id,
            "thread_id": thread_id,
            "user_query": "CLM-2026-005 为什么凭证生成失败？",
            "messages": [{"role": "user", "content": "CLM-2026-005 为什么凭证生成失败？"}],
        },
        {"configurable": {"thread_id": thread_id}},
    )
    assert result["__interrupt__"]
    approved = graph.invoke(
        Command(resume={"decision": "approve"}),
        {"configurable": {"thread_id": thread_id}},
    )
    assert approved["approval_result"] == "approved"
    assert approved["ticket_result"]["run_id"] == run_id
    decisions = [event for event in runs.events(run_id) if event["event_type"] == "human_decision"]
    assert len(decisions) == 1
