from fastapi import APIRouter, Request

router = APIRouter(tags=["system"])


@router.get("/health")
def health(request: Request):
    settings = request.app.state.settings
    model_configured = settings.llm_provider == "deterministic" or bool(settings.llm_api_key)
    retrieval_configured = (
        settings.retrieval_provider == "lexical" or bool(settings.effective_embedding_api_key)
    )
    return {
        "status": "ok" if model_configured and retrieval_configured else "degraded",
        "service": "agent-api",
        "llm_provider": settings.llm_provider,
        "retrieval_provider": settings.retrieval_provider,
        "model_configured": model_configured,
        "retrieval_configured": retrieval_configured,
        "data_classification": "synthetic",
    }
