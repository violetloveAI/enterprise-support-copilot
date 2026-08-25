from fastapi.testclient import TestClient

from services.mock_erp.app.database import seed_database
from services.mock_erp.app.main import app


def test_mock_erp_reads_and_idempotent_ticket(monkeypatch, tmp_path):
    monkeypatch.setenv("ERP_DB_PATH", str(tmp_path / "erp.db"))
    seed_database(force=True)
    with TestClient(app) as client:
        claim = client.get("/erp/claims/CLM-2026-005/status")
        assert claim.status_code == 200
        assert claim.json()["status"] == "APPROVED"
        payload = {
            "run_id": "run-12345678",
            "claim_id": "CLM-2026-005",
            "summary": "凭证期间关闭",
            "category": "voucher_config",
            "risk_level": "medium",
            "evidence": ["FI_PERIOD_CLOSED"],
        }
        first = client.post("/erp/tickets", json=payload)
        second = client.post("/erp/tickets", json=payload)
        assert first.status_code == 201
        assert second.json()["ticket_id"] == first.json()["ticket_id"]
        assert second.json()["idempotent_replay"] is True


def test_unknown_claim_returns_structured_404(monkeypatch, tmp_path):
    monkeypatch.setenv("ERP_DB_PATH", str(tmp_path / "erp.db"))
    seed_database(force=True)
    with TestClient(app) as client:
        response = client.get("/erp/claims/CLM-2099-999/status")
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "CLAIM_NOT_FOUND"
