from __future__ import annotations

import json
import re
from pathlib import Path

START = "<!-- EVAL_METRICS_START -->"
END = "<!-- EVAL_METRICS_END -->"
BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BACKEND_ROOT.parent


def update(
    readme: Path = REPOSITORY_ROOT / "README.md",
    report: Path = BACKEND_ROOT / "evals/results/latest.json",
) -> None:
    result = json.loads(report.read_text(encoding="utf-8"))
    metrics = result["metrics"]
    block = f"""{START}
Actual run: `{result["generated_at"]}` · provider `{result["provider"]}` · model
`{result["model"]}` · {result["case_count"]} cases ·
{result["failed_executions"]} execution failures.

| Metric | Actual score |
|---|---:|
| Classification accuracy | {metrics["classification_accuracy"]:.2%} |
| Tool selection accuracy | {metrics["tool_selection_accuracy"]:.2%} |
| Retrieval hit@3 | {metrics["retrieval_hit_at_3"]:.2%} |
| Escalation accuracy | {metrics["escalation_accuracy"]:.2%} |
| Citation coverage | {metrics["citation_coverage"]:.2%} |
| Evidence reference validity | {metrics["evidence_reference_validity"]:.2%} |
{END}"""
    text = readme.read_text(encoding="utf-8")
    updated = re.sub(f"{re.escape(START)}.*?{re.escape(END)}", block, text, flags=re.S)
    readme.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    update()
