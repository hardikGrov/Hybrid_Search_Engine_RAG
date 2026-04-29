from types import SimpleNamespace

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

    results = search_service.search_documents("apple", top_k=2)
    results_by_doc_id = {result["doc_id"]: result for result in results}

    assert bm25.calls == [("apple", 2)]
    assert vector.calls == [("apple", 2)]
    assert results_by_doc_id == {
        "shared": {
            "doc_id": "shared",
            "title": "Shared",
            "bm25_score": 2.5,
            "vector_score": 0.8,
        },
        "bm25-only": {
            "doc_id": "bm25-only",
            "title": "BM25 Only",
            "bm25_score": 1.5,
            "vector_score": 0,
        },
        "vector-only": {
            "doc_id": "vector-only",
            "title": "Vector Only",
            "bm25_score": 0,
            "vector_score": 0.7,
        },
    }
