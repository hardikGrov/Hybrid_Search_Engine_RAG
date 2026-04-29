from types import SimpleNamespace

import pytest

from backend.app.services import search_service


class FakeIndex:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def search(self, query, top_k):
        self.calls.append((query, top_k))
        return self.results


def test_search_documents_merges_bm25_and_vector_scores(monkeypatch):
    bm25 = FakeIndex(
        [
            SimpleNamespace(
                doc_id="shared",
                score=2.5,
                document={"doc_id": "shared", "title": "Shared"},
            ),
            SimpleNamespace(
                doc_id="bm25-only",
                score=1.5,
                document={"doc_id": "bm25-only", "title": "BM25 Only"},
            ),
        ]
    )
    vector = FakeIndex(
        [
            SimpleNamespace(
                doc_id="shared",
                title="Shared",
                score=0.8,
                document={"doc_id": "shared", "title": "Shared"},
            ),
            SimpleNamespace(
                doc_id="vector-only",
                title="Vector Only",
                score=0.7,
                document={"doc_id": "vector-only", "title": "Vector Only"},
            ),
        ]
    )

    monkeypatch.setattr(search_service, "get_bm25", lambda: bm25)
    monkeypatch.setattr(search_service, "get_vector", lambda: vector)
    monkeypatch.setattr(search_service, "get_docs", lambda: [{}, {}, {}])

    results = search_service.search_documents("apple", top_k=2)
    results_by_doc_id = {result["doc_id"]: result for result in results}

    assert bm25.calls == [("apple", 3)]
    assert vector.calls == [("apple", 3)]
    assert [result["doc_id"] for result in results] == ["shared", "vector-only"]
    assert results_by_doc_id == {
        "shared": {
            "doc_id": "shared",
            "title": "Shared",
            "bm25_score": 2.5,
            "vector_score": 0.8,
            "bm25_norm": 1.0,
            "vector_norm": 1.0,
            "hybrid_score": 1.0,
        },
        "vector-only": {
            "doc_id": "vector-only",
            "title": "Vector Only",
            "bm25_score": 0,
            "vector_score": 0.7,
            "bm25_norm": 0.0,
            "vector_norm": pytest.approx(0.875),
            "hybrid_score": pytest.approx(0.4375),
        },
    }


def test_search_documents_uses_custom_alpha_and_sorts_by_hybrid_score(monkeypatch):
    bm25 = FakeIndex(
        [
            SimpleNamespace(doc_id="bm25-first", score=2.0, document={"title": "BM25 First"}),
            SimpleNamespace(doc_id="shared", score=1.0, document={"title": "Shared"}),
        ]
    )
    vector = FakeIndex(
        [
            SimpleNamespace(doc_id="shared", title="Shared", score=0.2),
            SimpleNamespace(doc_id="vector-only", title="Vector Only", score=1.0),
        ]
    )

    monkeypatch.setattr(search_service, "get_bm25", lambda: bm25)
    monkeypatch.setattr(search_service, "get_vector", lambda: vector)
    monkeypatch.setattr(search_service, "get_docs", lambda: [{}, {}, {}])

    results = search_service.search_documents("apple", top_k=2, alpha=0.25)
    results_by_doc_id = {result["doc_id"]: result for result in results}

    assert [result["doc_id"] for result in results] == ["vector-only", "shared"]
    assert results_by_doc_id["shared"]["hybrid_score"] == pytest.approx(0.275)
    assert results_by_doc_id["vector-only"]["hybrid_score"] == 0.75


def test_search_documents_breaks_hybrid_score_ties_by_doc_id(monkeypatch):
    bm25 = FakeIndex(
        [
            SimpleNamespace(doc_id="doc_b", score=1.0, document={"title": "B"}),
            SimpleNamespace(doc_id="doc_a", score=1.0, document={"title": "A"}),
        ]
    )
    vector = FakeIndex([])

    monkeypatch.setattr(search_service, "get_bm25", lambda: bm25)
    monkeypatch.setattr(search_service, "get_vector", lambda: vector)
    monkeypatch.setattr(search_service, "get_docs", lambda: [{}, {}])

    results = search_service.search_documents("apple", top_k=2)

    assert [result["doc_id"] for result in results] == ["doc_a", "doc_b"]


def test_normalize_scores_returns_empty_list_for_empty_input():
    assert search_service.normalize_scores([]) == []


def test_normalize_scores_returns_zeroes_when_all_scores_are_equal():
    assert search_service.normalize_scores([4.0, 4.0, 4.0]) == [0, 0, 0]


def test_normalize_scores_uses_min_max_normalization():
    assert search_service.normalize_scores([2.0, 4.0, 6.0]) == [0.0, 0.5, 1.0]
