from services.agent_api.app.core.config import Settings
from services.agent_api.app.rag.retriever import KnowledgeRetriever


def test_interface_query_retrieves_interface_manual():
    settings = Settings(llm_provider="deterministic")
    rows = KnowledgeRetriever(settings).search("接口 HTTP_504 重试三次", "interface_system", 3)
    assert "KB-010" in {row["doc_id"] for row in rows}
    assert all(row["chunk_id"] and row["section"] for row in rows)
