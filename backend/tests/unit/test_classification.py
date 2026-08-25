import pytest

from services.agent_api.app.agent.model_gateway import ModelGateway
from services.agent_api.app.core.config import Settings


@pytest.mark.parametrize(
    ("query", "category"),
    [
        ("报销单怎么新建？", "operation"),
        ("用户 U1002 没有权限", "permission"),
        ("CLM-2026-003 审批卡住", "approval"),
        ("U1004 成本中心主数据为空", "master_data"),
        ("CLM-2026-005 凭证过账失败", "voucher_config"),
        ("CLM-2026-007 附件同步接口504", "interface_system"),
    ],
)
def test_deterministic_classification(query, category):
    issue = ModelGateway(Settings(llm_provider="deterministic")).analyze(query)
    assert issue.category == category


def test_missing_identifier_is_never_invented():
    issue = ModelGateway(Settings(llm_provider="deterministic")).analyze("我的审批一直卡住")
    assert issue.claim_id is None
    assert issue.missing_fields == ["claim_id"]
