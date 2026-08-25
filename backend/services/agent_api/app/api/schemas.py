from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=3, max_length=2000)
    thread_id: str | None = None


class ResumeRequest(BaseModel):
    decision: Literal["approve", "reject"]


class RunResponse(BaseModel):
    run_id: str
    thread_id: str
    status: str
    clarification_question: str | None = None
    diagnosis: dict[str, Any] | None = None
    pending_approval: dict[str, Any] | None = None
    ticket: dict[str, Any] | None = None
    retrieved_sources: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)
    llm_provider: str
    retrieval_provider: str
