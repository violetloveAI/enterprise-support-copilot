from services.agent_api.app.core.config import get_settings
from services.agent_api.app.rag.indexer import build_index

if __name__ == "__main__":
    settings = get_settings()
    count = build_index(settings)
    print(f"Indexed {count} chunks using provider={settings.llm_provider}")
