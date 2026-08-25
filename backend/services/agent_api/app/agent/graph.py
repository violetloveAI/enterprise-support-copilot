from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from ..core.config import Settings
from ..observability.events import RunRepository
from ..persistence.checkpoint import create_checkpointer
from ..rag.retriever import KnowledgeRetriever
from ..tools.erp_client import ERPClient, ERPClientProtocol
from ..tools.executor import AuditedToolExecutor
from .model_gateway import ModelGateway
from .nodes import AgentNodes
from .routing import after_analyze, after_diagnose
from .state import AgentState


def build_graph(
    settings: Settings,
    *,
    erp_client: ERPClientProtocol | None = None,
    runs: RunRepository | None = None,
):
    runs = runs or RunRepository(settings.copilot_db_path)
    erp_client = erp_client or ERPClient(settings.mock_erp_base_url)
    nodes = AgentNodes(
        ModelGateway(settings),
        KnowledgeRetriever(settings),
        AuditedToolExecutor(erp_client, runs),
        erp_client,
        runs,
    )
    builder = StateGraph(AgentState)
    builder.add_node("analyze", nodes.analyze)
    builder.add_node("clarify", nodes.clarify)
    builder.add_node("retrieve", nodes.retrieve)
    builder.add_node("plan_tools", nodes.plan_tools)
    builder.add_node("execute_tools", nodes.execute_tools)
    builder.add_node("diagnose", nodes.diagnose)
    builder.add_node("approval", nodes.approval)
    builder.add_node("complete", nodes.complete)
    builder.add_edge(START, "analyze")
    builder.add_conditional_edges(
        "analyze", after_analyze, {"clarify": "clarify", "retrieve": "retrieve"}
    )
    builder.add_edge("clarify", END)
    builder.add_edge("retrieve", "plan_tools")
    builder.add_edge("plan_tools", "execute_tools")
    builder.add_edge("execute_tools", "diagnose")
    builder.add_conditional_edges(
        "diagnose", after_diagnose, {"approval": "approval", "complete": "complete"}
    )
    builder.add_edge("approval", END)
    builder.add_edge("complete", END)
    checkpointer = create_checkpointer(settings.copilot_db_path.with_name("checkpoints.db"))
    return builder.compile(checkpointer=checkpointer), runs
