import pytest

from hybrid_search.index.bm25 import BM25Index, BM25Result, tokenize


def test_tokenize_lowercases_and_removes_punctuation():
    assert tokenize("Hybrid Search, SEARCH! v2") == ["hybrid", "search", "search", "v2"]


def test_fit_stores_document_statistics():
    documents = [
        {"doc_id": "doc_0", "text": "alpha beta beta"},
        {"doc_id": "doc_1", "text": "beta gamma"},
    ]

    index = BM25Index().fit(documents)

    assert index.documents == documents
    assert index.document_lengths == [3, 2]
    assert index.average_document_length == pytest.approx(2.5)
    assert index.document_frequencies["alpha"] == 1
    assert index.document_frequencies["beta"] == 2
    assert index.term_frequencies[0]["beta"] == 2


def test_search_ranks_documents_by_bm25_score():
    documents = [
        {"doc_id": "fruit", "text": "apple banana apple apple"},
        {"doc_id": "vehicle", "text": "car truck train"},
        {"doc_id": "mixed", "text": "apple car"},
    ]

    results = BM25Index().fit(documents).search("apple", top_k=2)

    assert [result.doc_id for result in results] == ["fruit", "mixed"]
    assert all(isinstance(result, BM25Result) for result in results)
    assert results[0].score > results[1].score > 0
    assert results[0].document == documents[0]


def test_search_is_case_insensitive_and_ignores_query_punctuation():
    documents = [
        {"doc_id": "python", "text": "Python powers retrieval pipelines."},
        {"doc_id": "java", "text": "Java powers enterprise systems."},
    ]

    results = BM25Index().fit(documents).search("PYTHON!!!", top_k=1)

    assert results[0].doc_id == "python"
    assert results[0].score > 0


def test_search_returns_zero_scores_for_unknown_terms():
    documents = [
        {"doc_id": "doc_0", "text": "alpha beta"},
        {"doc_id": "doc_1", "text": "gamma delta"},
    ]

    results = BM25Index().fit(documents).search("missing", top_k=2)

    assert [result.score for result in results] == [0.0, 0.0]


def test_search_uses_position_as_doc_id_when_document_has_no_doc_id():
    results = BM25Index().fit([{"text": "alpha"}]).search("alpha")

    assert results[0].doc_id == "0"


def test_fit_rejects_empty_document_collection():
    with pytest.raises(ValueError, match="at least one document"):
        BM25Index().fit([])


def test_search_requires_fit():
    with pytest.raises(ValueError, match="fit before searching"):
        BM25Index().search("alpha")


def test_score_requires_valid_document_index():
    index = BM25Index().fit([{"doc_id": "doc_0", "text": "alpha"}])

    with pytest.raises(IndexError, match="out of range"):
        index.score("alpha", 1)


def test_search_rejects_non_positive_top_k():
    index = BM25Index().fit([{"doc_id": "doc_0", "text": "alpha"}])

    with pytest.raises(ValueError, match="top_k"):
        index.search("alpha", top_k=0)


def test_constructor_validates_parameters():
    with pytest.raises(ValueError, match="k1"):
        BM25Index(k1=0)

    with pytest.raises(ValueError, match="b"):
        BM25Index(b=1.5)
