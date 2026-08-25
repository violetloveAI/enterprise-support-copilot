from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from ..observability.events import RunRepository
from .erp_client import ERPClientProtocol


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


class AuditedToolExecutor:
    allowed_read_tools = {
        "get_claim_status",
        "get_user_permissions",
        "get_approval_flow",
        "get_voucher_status",
        "get_interface_log",
    }

    def __init__(self, client: ERPClientProtocol, runs: RunRepository):
        self.client = client
        self.runs = runs

    def execute(self, run_id: str, call: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            parsed = ToolCall.model_validate(call)
            if parsed.name not in self.allowed_read_tools:
                raise ValueError(f"Tool {parsed.name} is not an approved read tool")
            self._validate_required_args(parsed)
            result = self.client.call(parsed.name, parsed.args)
            event = {
                "evidence_id": f"TOOL-{parsed.name}",
                "tool_name": parsed.name,
                "arguments": parsed.args,
                "ok": "error" not in result,
                "result": result,
            }
            self.runs.event(
                run_id,
                "tool_result",
                "execute_tools",
                duration_ms=int((time.perf_counter() - started) * 1000),
                tool_name=parsed.name,
                arguments=parsed.args,
                result_summary=result,
            )
            return event
        except (ValidationError, ValueError, httpx_error()) as exc:
            self.runs.event(
                run_id,
                "tool_error",
                "execute_tools",
                status="failed",
                duration_ms=int((time.perf_counter() - started) * 1000),
                error=str(exc),
            )
            return {
                "evidence_id": f"TOOL-{call.get('name', 'unknown')}",
                "tool_name": call.get("name", "unknown"),
                "arguments": call.get("args", {}),
                "ok": False,
                "error": str(exc),
            }

    @staticmethod
    def _validate_required_args(call: ToolCall) -> None:
        if call.name == "get_user_permissions" and not call.args.get("user_id"):
            raise ValueError("user_id is required")
        if call.name in {
            "get_claim_status",
            "get_approval_flow",
            "get_voucher_status",
        } and not call.args.get("claim_id"):
            raise ValueError("claim_id is required")
        if call.name == "get_interface_log" and not any(call.args.values()):
            raise ValueError("At least one interface log filter is required")


def httpx_error():
    import httpx

    return httpx.HTTPError
