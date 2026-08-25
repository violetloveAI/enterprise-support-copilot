from __future__ import annotations

from statistics import mean


def exact_match(expected, actual) -> float:
    return float(expected == actual)


def set_exact_match(expected, actual) -> float:
    return float(set(expected) == set(actual))


def retrieval_hit_at_3(expected_docs: list[str], actual_docs: list[str]) -> float | None:
    if not expected_docs:
        return None
    return float(bool(set(expected_docs) & set(actual_docs[:3])))


def aggregate(rows: list[dict]) -> dict[str, float]:
    metric_names = [
        "classification_accuracy",
        "tool_selection_accuracy",
        "retrieval_hit_at_3",
        "escalation_accuracy",
        "citation_coverage",
        "evidence_reference_validity",
    ]
    return {
        name: round(mean(values), 4)
        if (values := [row[name] for row in rows if row.get(name) is not None])
        else 0.0
        for name in metric_names
    }
