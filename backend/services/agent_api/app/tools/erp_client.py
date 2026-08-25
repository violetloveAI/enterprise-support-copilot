from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[4]


class ERPClientProtocol(Protocol):
    def call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


class ERPClient:
    """Production adapter: every ERP read/write crosses a REST/JSON boundary."""

    def __init__(self, base_url: str, timeout: float = 5.0):
        if not base_url.startswith(("http://", "https://")):
            base_url = f"http://{base_url}"
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        claim_id = arguments.get("claim_id")
        user_id = arguments.get("user_id")
        routes = {
            "get_claim_status": ("GET", f"/erp/claims/{claim_id}/status"),
            "get_user_permissions": ("GET", f"/erp/users/{user_id}/permissions"),
            "get_approval_flow": ("GET", f"/erp/claims/{claim_id}/approval-flow"),
            "get_voucher_status": ("GET", f"/erp/claims/{claim_id}/voucher-status"),
            "get_interface_log": ("GET", "/erp/interfaces/logs"),
            "create_ticket": ("POST", "/erp/tickets"),
        }
        if tool_name not in routes:
            raise ValueError(f"Unknown ERP tool: {tool_name}")
        method, path = routes[tool_name]
        # Internal service traffic must not inherit a developer machine's proxy settings.
        with httpx.Client(base_url=self.base_url, timeout=self.timeout, trust_env=False) as client:
            response = (
                client.get(path, params=arguments)
                if method == "GET"
                else client.post(path, json=arguments)
            )
        response.raise_for_status()
        return response.json()


class SyntheticFixtureERPClient:
    """Offline test adapter. Never used by the running API service."""

    def __init__(self, data_path: str | Path | None = None):
        base = Path(data_path) if data_path else BACKEND_ROOT / "data/synthetic"
        self.data = {
            name: json.loads((base / f"{name}.json").read_text(encoding="utf-8"))
            for name in (
                "users",
                "permissions",
                "claims",
                "approval_flows",
                "vouchers",
                "interface_logs",
                "tickets",
            )
        }

    @staticmethod
    def _one(rows: list[dict], key: str, value: str) -> dict:
        return next((row for row in rows if row.get(key) == value), {"error": "NOT_FOUND"})

    def call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        claim_id, user_id = arguments.get("claim_id"), arguments.get("user_id")
        if tool_name == "get_claim_status":
            return self._one(self.data["claims"], "claim_id", claim_id)
        if tool_name == "get_user_permissions":
            return {
                "user": self._one(self.data["users"], "user_id", user_id),
                "permissions": self._one(self.data["permissions"], "user_id", user_id),
            }
        if tool_name == "get_approval_flow":
            return self._one(self.data["approval_flows"], "claim_id", claim_id)
        if tool_name == "get_voucher_status":
            return self._one(self.data["vouchers"], "claim_id", claim_id)
        if tool_name == "get_interface_log":
            filters = {k: v for k, v in arguments.items() if v is not None}
            return {
                "items": [
                    row
                    for row in self.data["interface_logs"]
                    if all(row.get(key) == value for key, value in filters.items())
                ]
            }
        if tool_name == "create_ticket":
            return {"ticket_id": "TKT-OFFLINE-0001", **arguments, "status": "OPEN"}
        raise ValueError(f"Unknown ERP tool: {tool_name}")
