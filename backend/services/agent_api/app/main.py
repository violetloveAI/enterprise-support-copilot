from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agent.graph import build_graph
from .api.routes import chat, health, runs
from .core.config import get_settings
from .observability.logging import configure_logging
from .rag.indexer import build_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    if (
        settings.retrieval_provider == "vector"
        and settings.auto_build_index
        and bool(settings.effective_embedding_api_key)
        and not settings.chroma_path.exists()
    ):
        build_index(settings)
    graph, repository = build_graph(settings)
    app.state.settings = settings
    app.state.graph = graph
    app.state.runs = repository
    yield


app = FastAPI(
    title="Enterprise Support Copilot API",
    version="2.0.0",
    description="Evidence-grounded diagnostic agent for a synthetic enterprise expense system.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().parsed_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat.router)
app.include_router(runs.router)
app.include_router(health.router)
