from services.agent_api.app.core.config import Settings


def test_embedding_provider_can_differ_from_chat_provider():
    settings = Settings(
        llm_provider="openai_compatible",
        llm_api_key="chat-key",
        llm_base_url="https://chat.example/v1",
        embedding_api_key="embedding-key",
        embedding_base_url="https://embedding.example/v1",
    )
    assert settings.effective_embedding_api_key == "embedding-key"
    assert settings.effective_embedding_base_url == "https://embedding.example/v1"


def test_cors_origins_are_parsed_from_comma_separated_env_value():
    settings = Settings(cors_origins="http://localhost:5173, https://demo.example")
    assert settings.parsed_cors_origins == ["http://localhost:5173", "https://demo.example"]
