from __future__ import annotations

import json
import re
from typing import Any

from langchain_openai import ChatOpenAI

from ..core.config import Settings
from ..tools.definitions import READ_TOOLS
from .prompts import ANALYZE_PROMPT, DIAGNOSIS_PROMPT, TOOL_PROMPT
from .state import Citation, Diagnosis, Evidence, StructuredIssue

CATEGORY_LABELS = {
    "operation": "操作问题",
    "permission": "权限问题",
    "approval": "审批流程问题",
    "master_data": "数据/主数据问题",
    "voucher_config": "凭证/配置问题",
    "interface_system": "接口/系统异常",
}


class ModelGateway:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._model: ChatOpenAI | None = None

    @property
    def model(self) -> ChatOpenAI:
        if self._model is None:
            self.settings.validate_runtime()
            model_kwargs = {
                "model": self.settings.llm_model,
                "api_key": self.settings.llm_api_key,
                "base_url": self.settings.llm_base_url,
            }
            if self.settings.llm_temperature is not None:
                model_kwargs["temperature"] = self.settings.llm_temperature
            self._model = ChatOpenAI(**model_kwargs)
        return self._model

    def analyze(self, query: str) -> StructuredIssue:
        if self.settings.llm_provider == "deterministic":
            return self._deterministic_analyze(query)
        return self.model.with_structured_output(StructuredIssue).invoke(
            ANALYZE_PROMPT.format(query=query)
        )

    def choose_tools(self, query: str, issue: StructuredIssue) -> list[dict[str, Any]]:
        if self.settings.llm_provider == "deterministic":
            return self._deterministic_tools(issue, query)
        response = self.model.bind_tools(READ_TOOLS, tool_choice="auto").invoke(
            TOOL_PROMPT.format(query=query, issue=issue.model_dump_json())
        )
        return [{"name": call["name"], "args": call["args"]} for call in response.tool_calls]

    def diagnose(
        self,
        query: str,
        issue: StructuredIssue,
        chunks: list[dict[str, Any]],
        tool_results: list[dict[str, Any]],
    ) -> Diagnosis:
        if self.settings.llm_provider == "deterministic":
            return self._deterministic_diagnosis(issue, chunks, tool_results)
        return self.model.with_structured_output(Diagnosis).invoke(
            DIAGNOSIS_PROMPT.format(
                query=query,
                category=issue.category,
                chunks=json.dumps(chunks, ensure_ascii=False),
                tool_results=json.dumps(tool_results, ensure_ascii=False),
            )
        )

    @staticmethod
    def _deterministic_analyze(query: str) -> StructuredIssue:
        normalized = query.lower()
        rules = [
            (
                "interface_system",
                ["接口", "同步", "504", "网关", "系统异常", "超时", "correlation"],
            ),
            ("voucher_config", ["凭证", "过账", "期间", "科目", "税码", "fi_period"]),
            ("permission", ["权限", "角色", "无法提交", "按钮", "看不到", "账号锁定"]),
            ("approval", ["审批", "待办", "卡住", "代理", "驳回", "主管"]),
            ("master_data", ["主数据", "成本中心", "公司代码", "银行信息", "字段为空"]),
        ]
        category = "operation"
        for candidate, words in rules:
            if any(word in normalized for word in words):
                category = candidate
                break
        claim = re.search(r"CLM-\d{4}-\d{3}", query, re.IGNORECASE)
        user = re.search(r"U\d{4}", query, re.IGNORECASE)
        error = re.search(r"(?:HTTP_\d+|FI_[A-Z_]+|[A-Z]+_[A-Z_]+)", query)
        issue = StructuredIssue(
            summary=query[:160],
            category=category,
            claim_id=claim.group(0).upper() if claim else None,
            user_id=user.group(0).upper() if user else None,
            error_code=error.group(0) if error else None,
        )
        required = {
            "permission": ["user_id"],
            "approval": ["claim_id"],
            "voucher_config": ["claim_id"],
            "interface_system": ["claim_id"],
            "master_data": ["user_id_or_claim_id"],
            "operation": [],
        }
        incident_signals = [
            "帮我",
            "我的",
            "用户",
            "报销单",
            "卡住",
            "失败",
            "异常",
            "核实",
            "突然",
            "一直",
            "不让我",
        ]
        needs_instance_lookup = any(signal in query for signal in incident_signals)
        issue.missing_fields = [
            field
            for field in (required[category] if needs_instance_lookup else [])
            if (field == "user_id" and not issue.user_id)
            or (field == "claim_id" and not issue.claim_id)
            or (field == "user_id_or_claim_id" and not (issue.user_id or issue.claim_id))
        ]
        return issue

    @staticmethod
    def _deterministic_tools(issue: StructuredIssue, query: str) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []
        if issue.category == "operation" and issue.claim_id:
            calls.append({"name": "get_claim_status", "args": {"claim_id": issue.claim_id}})
        elif issue.category == "permission":
            if issue.user_id:
                calls.append({"name": "get_user_permissions", "args": {"user_id": issue.user_id}})
            if issue.claim_id:
                calls.append({"name": "get_claim_status", "args": {"claim_id": issue.claim_id}})
        elif issue.category == "approval" and issue.claim_id:
            calls.extend(
                [
                    {"name": "get_claim_status", "args": {"claim_id": issue.claim_id}},
                    {"name": "get_approval_flow", "args": {"claim_id": issue.claim_id}},
                ]
            )
        elif issue.category == "master_data":
            if issue.user_id:
                calls.append({"name": "get_user_permissions", "args": {"user_id": issue.user_id}})
            if issue.claim_id:
                calls.append({"name": "get_claim_status", "args": {"claim_id": issue.claim_id}})
        elif issue.category == "voucher_config" and issue.claim_id:
            calls.extend(
                [
                    {"name": "get_claim_status", "args": {"claim_id": issue.claim_id}},
                    {"name": "get_voucher_status", "args": {"claim_id": issue.claim_id}},
                ]
            )
        elif issue.category == "interface_system" and issue.claim_id:
            calls.extend(
                [
                    {"name": "get_claim_status", "args": {"claim_id": issue.claim_id}},
                    {"name": "get_interface_log", "args": {"claim_id": issue.claim_id}},
                ]
            )
        return calls

    @staticmethod
    def _deterministic_diagnosis(
        issue: StructuredIssue,
        chunks: list[dict[str, Any]],
        tool_results: list[dict[str, Any]],
    ) -> Diagnosis:
        valid_results = [row for row in tool_results if row.get("ok")]
        evidence = [
            Evidence(
                evidence_id=f"E-{index:02d}",
                source_type="tool",
                source_id=row["evidence_id"],
                statement=(
                    f"{row['tool_name']} 返回：{json.dumps(row['result'], ensure_ascii=False)}"
                ),
            )
            for index, row in enumerate(valid_results, start=1)
        ]
        citations = [
            Citation(
                doc_id=row["doc_id"],
                chunk_id=row["chunk_id"],
                title=row["title"],
                section=row["section"],
            )
            for row in chunks[:3]
        ]
        causes: list[str] = []
        steps = ["核对问题中的用户编号、报销单号和发生时间。"]
        escalation = bool(valid_results) and issue.category in {
            "permission",
            "master_data",
            "voucher_config",
        }
        risk = "medium" if escalation else "low"
        serialized = json.dumps(valid_results, ensure_ascii=False)
        if "TRAVEL_CLAIM" in serialized and "missing_permissions" in serialized:
            causes.append("用户缺少差旅报销业务角色，提交权限校验失败。")
            steps.append("由权限管理员核对并按审批流程补充 TRAVEL_CLAIM 角色。")
            escalation = True
        elif "FI_PERIOD_CLOSED" in serialized:
            causes.append("报销单计划过账日期所在财务期间未开放。")
            steps.append("由财务控制岗核对公司代码和过账期间，修复后重新触发凭证。")
            escalation, risk = True, "medium"
        elif "HTTP_504" in serialized:
            causes.append("附件同步调用下游网关超时，且重试次数已达到上限。")
            steps.append("携带 correlation ID 升级接口支持，停止继续重复重放。")
            escalation, risk = True, "high"
        elif "成本中心为空" in serialized:
            causes.append("员工成本中心主数据为空，提交校验无法通过。")
            steps.append("由主数据维护人补全有效成本中心并等待同步。")
            escalation = True
        elif '"status": "WAITING"' in serialized and "PENDING" in serialized:
            causes.append("报销单停留在当前审批待办，待办已超过配置的处理时限。")
            steps.append("核对待办人账号状态；需要转派时由流程管理员处理。")
            escalation = True
        elif valid_results:
            causes.append("工具结果显示了当前业务状态，但没有发现可确认的系统根因。")
            steps.append("按引用手册继续核对状态和相关配置。")
        else:
            causes.append("当前没有足够的系统查询证据，无法判断具体根因。")
            steps.append("补充报销单号、用户编号或错误发生时间后重新诊断。")
        if issue.category == "operation" and not valid_results:
            causes = ["该问题可先按操作手册核对页面状态与必填项；尚无证据表明系统异常。"]
        confidence = 0.88 if valid_results and causes else 0.45
        uncertainty = (
            None
            if valid_results
            else "没有足够的 ERP 查询证据，当前结论仅为操作指引，无法确认系统根因。"
        )
        return Diagnosis(
            category=issue.category,
            category_label=CATEGORY_LABELS[issue.category],
            possible_causes=causes,
            evidence=evidence,
            citations=citations,
            troubleshooting_steps=steps,
            risk_level=risk,
            escalation_required=escalation,
            escalation_reason="需要受控角色执行变更或进一步排查。" if escalation else None,
            confidence=confidence,
            uncertainty_statement=uncertainty,
        )
