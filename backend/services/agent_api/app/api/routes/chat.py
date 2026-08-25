from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from langgraph.types import Command

from ..schemas import ChatRequest, ResumeRequest, RunResponse

router = APIRouter(prefix="/api/v1", tags=["copilot"])


def _interrupt_value(result: dict):
    values = result.get("__interrupt__", [])
    if not values:
        return None
    item = values[0]
    return getattr(item, "value", item)


def _response(run_id: str, thread_id: str, result: dict, request: Request) -> RunResponse:
    settings = request.app.state.settings
    return RunResponse(
        run_id=run_id,
        thread_id=thread_id,
        status=result.get("status", "running"),
        clarification_question=result.get("clarification_question"),
        diagnosis=result.get("diagnosis"),
        pending_approval=_interrupt_value(result),
        ticket=result.get("ticket_result"),
        retrieved_sources=result.get("retrieved_chunks", []),
        tool_calls=result.get("tool_results", []),
        events=request.app.state.runs.events(run_id),
        llm_provider=settings.llm_provider,
        retrieval_provider=settings.retrieval_provider,
    )


@router.post("/chat/invoke", response_model=RunResponse)
def invoke(payload: ChatRequest, request: Request):
    run_id = str(uuid4())
    thread_id = payload.thread_id or str(uuid4())
    graph, runs = request.app.state.graph, request.app.state.runs
    runs.start_run(run_id, thread_id, payload.message)
    try:
        result = graph.invoke(
            {
                "run_id": run_id,
                "thread_id": thread_id,
                "user_query": payload.message,
                "messages": [{"role": "user", "content": payload.message}],
                "errors": [],
            },
            config={"configurable": {"thread_id": thread_id}},
        )
    except RuntimeError as exc:
        runs.event(run_id, "configuration_error", "invoke", status="failed", error=str(exc))
        runs.finish(run_id, "failed", {"error": str(exc)})
        raise HTTPException(503, detail=str(exc)) from exc
    status = (
        "awaiting_approval" if result.get("__interrupt__") else result.get("status", "completed")
    )
    result["status"] = status
    runs.finish(run_id, status, result)
    return _response(run_id, thread_id, result, request)


@router.post("/runs/{run_id}/resume", response_model=RunResponse)
def resume(run_id: str, payload: ResumeRequest, request: Request):
    graph, runs = request.app.state.graph, request.app.state.runs
    run = runs.get(run_id)
    if not run:
        raise HTTPException(404, detail="Run not found")
    if run["status"] != "awaiting_approval":
        raise HTTPException(409, detail="Run is not awaiting approval")
    thread_id = run["thread_id"]
    result = graph.invoke(
        Command(resume={"decision": payload.decision}),
        config={"configurable": {"thread_id": thread_id}},
    )
    result["status"] = result.get("status", "completed")
    runs.finish(run_id, result["status"], result)
    return _response(run_id, thread_id, result, request)
