from typing import Literal

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    run_id: str = Field(min_length=8)
    claim_id: str | None = None
    user_id: str | None = None
    summary: str = Field(min_length=5, max_length=300)
    category: str
    risk_level: Literal["low", "medium", "high"]
    evidence: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: str
    detail: str
