from langchain_core.tools import tool


@tool
def get_claim_status(claim_id: str) -> dict:
    """查询指定报销单的当前状态、用户、金额、类型和系统提示。只读。"""
    raise RuntimeError("Tool execution is delegated to AuditedToolExecutor")


@tool
def get_user_permissions(user_id: str) -> dict:
    """查询指定用户的账号状态、公司代码、组织和报销角色。只读。"""
    raise RuntimeError("Tool execution is delegated to AuditedToolExecutor")


@tool
def get_approval_flow(claim_id: str) -> dict:
    """查询报销单审批节点、当前步骤、待办角色、处理人与截止时间。只读。"""
    raise RuntimeError("Tool execution is delegated to AuditedToolExecutor")


@tool
def get_voucher_status(claim_id: str) -> dict:
    """查询报销单财务凭证状态、凭证号和错误码。只读。"""
    raise RuntimeError("Tool execution is delegated to AuditedToolExecutor")


@tool
def get_interface_log(
    claim_id: str | None = None,
    interface: str | None = None,
    correlation_id: str | None = None,
) -> dict:
    """按报销单、接口或关联ID查询接口运行日志。至少提供一个过滤条件。只读。"""
    raise RuntimeError("Tool execution is delegated to AuditedToolExecutor")


@tool
def create_ticket(
    run_id: str,
    summary: str,
    category: str,
    risk_level: str,
    claim_id: str | None = None,
    user_id: str | None = None,
    evidence: list[str] | None = None,
) -> dict:
    """创建人工支持工单。此工具有写副作用，执行前必须获得用户明确批准。"""
    raise RuntimeError("Tool execution is delegated to AuditedToolExecutor")


READ_TOOLS = [
    get_claim_status,
    get_user_permissions,
    get_approval_flow,
    get_voucher_status,
    get_interface_log,
]
WRITE_TOOLS = [create_ticket]
ALL_TOOLS = READ_TOOLS + WRITE_TOOLS
