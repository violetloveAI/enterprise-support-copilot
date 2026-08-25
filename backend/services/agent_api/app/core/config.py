from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_ROOT / ".env", ".env"),
        extra="ignore",
    )

    llm_provider: Literal["openai_compatible", "deterministic"] = "deterministic"
    retrieval_provider: Literal["lexical", "vector"] = "lexical"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_api_key: str = ""
    embedding_base_url: str = ""
    llm_temperature: float | None = None
    mock_erp_base_url: str = "http://localhost:8001"
    copilot_db_path: Path = BACKEND_ROOT / "runtime/copilot.db"
    chroma_path: Path = BACKEND_ROOT / "runtime/chroma"
    knowledge_base_path: Path = BACKEND_ROOT / "knowledge_base"
    max_tool_rounds: int = Field(2, ge=1, le=4)
    rag_top_k: int = Field(3, ge=1, le=8)
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    auto_build_index: bool = True

    def validate_runtime(self) -> None:
        if self.llm_provider == "openai_compatible" and not self.llm_api_key:
            raise RuntimeError(
                "LLM_API_KEY is required when LLM_PROVIDER=openai_compatible. "
                "Use deterministic only for tests/offline demos."
            )
        if self.retrieval_provider == "vector" and not self.effective_embedding_api_key:
            raise RuntimeError(
                "An embedding API key is required when RETRIEVAL_PROVIDER=vector. "
                "Use lexical for the reproducible offline baseline."
            )

    @property
    def effective_embedding_api_key(self) -> str:
        return self.embedding_api_key or self.llm_api_key

    @property
    def effective_embedding_base_url(self) -> str:
        return self.embedding_base_url or self.llm_base_url

    @property
    def parsed_cors_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
