from .state import AgentState


def after_analyze(state: AgentState) -> str:
    return "clarify" if state.get("missing_fields") else "retrieve"


def after_tools(state: AgentState) -> str:
    return "diagnose"


def after_diagnose(state: AgentState) -> str:
    return "approval" if state.get("pending_action") else "complete"
