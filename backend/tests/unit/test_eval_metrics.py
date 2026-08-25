from evals.metrics import aggregate, retrieval_hit_at_3, set_exact_match


def test_tool_selection_uses_set_exact_match():
    assert set_exact_match(["a", "b"], ["b", "a"]) == 1
    assert set_exact_match(["a"], ["a", "b"]) == 0


def test_retrieval_metric_is_na_without_expected_docs():
    assert retrieval_hit_at_3([], ["KB-001"]) is None
    assert retrieval_hit_at_3(["KB-010"], ["KB-001", "KB-010"]) == 1


def test_aggregate_excludes_na():
    rows = [
        {
            "classification_accuracy": 1,
            "tool_selection_accuracy": 1,
            "retrieval_hit_at_3": None,
            "escalation_accuracy": 1,
            "citation_coverage": 1,
        },
        {
            "classification_accuracy": 0,
            "tool_selection_accuracy": 1,
            "retrieval_hit_at_3": 1,
            "escalation_accuracy": 1,
            "citation_coverage": 1,
        },
    ]
    assert aggregate(rows)["classification_accuracy"] == 0.5
    assert aggregate(rows)["retrieval_hit_at_3"] == 1.0
