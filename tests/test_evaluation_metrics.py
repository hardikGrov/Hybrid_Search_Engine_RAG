from evaluation.metrics import mean_reciprocal_rank
from evaluation.metrics import ndcg_at_k

import pytest


def test_mean_reciprocal_rank_uses_first_relevant_doc_rank():
    results = {"q1": ["doc_a", "doc_b", "doc_c"]}
    qrels = {"q1": ["doc_b", "doc_c"]}

    assert mean_reciprocal_rank(results, qrels) == 0.5


def test_mean_reciprocal_rank_scores_zero_when_no_relevant_doc_is_found():
    results = {"q1": ["doc_a", "doc_b"]}
    qrels = {"q1": ["doc_c"]}

    assert mean_reciprocal_rank(results, qrels) == 0


def test_mean_reciprocal_rank_averages_across_queries():
    results = {
        "q1": ["doc_a"],
        "q2": ["doc_b", "doc_c"],
        "q3": ["doc_d"],
    }
    qrels = {
        "q1": ["doc_a"],
        "q2": ["doc_c"],
        "q3": ["doc_missing"],
    }

    assert mean_reciprocal_rank(results, qrels) == 0.5


def test_mean_reciprocal_rank_returns_zero_for_empty_qrels():
    assert mean_reciprocal_rank({}, {}) == 0


def test_ndcg_at_k_returns_one_for_perfect_binary_ranking():
    results = {"q1": ["doc_a", "doc_b", "doc_c"]}
    qrels = {"q1": ["doc_a", "doc_b"]}

    assert ndcg_at_k(results, qrels, k=2) == 1.0


def test_ndcg_at_k_discounts_lower_ranked_relevant_docs():
    results = {"q1": ["doc_x", "doc_a", "doc_b"]}
    qrels = {"q1": ["doc_a", "doc_b"]}

    assert ndcg_at_k(results, qrels, k=3) == pytest.approx(0.6934264036172708)


def test_ndcg_at_k_scores_zero_when_no_relevant_doc_is_found():
    results = {"q1": ["doc_x", "doc_y"]}
    qrels = {"q1": ["doc_a"]}

    assert ndcg_at_k(results, qrels, k=2) == 0


def test_ndcg_at_k_averages_across_queries():
    results = {
        "q1": ["doc_a"],
        "q2": ["doc_x", "doc_b"],
    }
    qrels = {
        "q1": ["doc_a"],
        "q2": ["doc_b"],
    }

    assert ndcg_at_k(results, qrels, k=2) == pytest.approx(0.8154648767857288)


def test_ndcg_at_k_returns_zero_for_empty_or_non_positive_cases():
    assert ndcg_at_k({}, {}, k=10) == 0
    assert ndcg_at_k({"q1": ["doc_a"]}, {"q1": ["doc_a"]}, k=0) == 0
