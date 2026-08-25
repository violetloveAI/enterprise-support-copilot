from services.agent_api.app.agent.routing import after_analyze, after_diagnose


def test_routes_to_clarification_when_fields_missing():
    assert after_analyze({"missing_fields": ["claim_id"]}) == "clarify"


def test_routes_to_approval_only_for_pending_write():
    assert after_diagnose({"pending_action": {"name": "create_ticket"}}) == "approval"
    assert after_diagnose({"pending_action": None}) == "complete"
