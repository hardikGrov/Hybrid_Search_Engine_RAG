import json
from pathlib import Path
from hybrid_search.index.bm25 import BM25Index
from hybrid_search.index.vector import VectorIndex

DATA_PATH = Path("data/processed/docs.jsonl")

_docs = None
_bm25 = None
_vector = None


def get_docs():
    global _docs

    if _docs is not None:
        return _docs

    if not DATA_PATH.exists():
        raise RuntimeError("Processed data not found")

    _docs = []
    with open(DATA_PATH) as f:
        for line in f:
            _docs.append(json.loads(line))

    return _docs


def get_bm25():
    global _bm25

    if _bm25 is not None:
        return _bm25

    _bm25 = BM25Index().fit(get_docs())
    return _bm25


def get_vector():
    global _vector

    if _vector is not None:
        return _vector

    _vector = VectorIndex().fit(get_docs())
    return _vector


def normalize_scores(scores: list[float]):
    if not scores:
        return []

    min_score = min(scores)
    max_score = max(scores)
    score_range = max_score - min_score
    if score_range == 0:
        return [0 for _ in scores]

    return [(score - min_score) / score_range for score in scores]


def search_documents(query: str, top_k: int):
    if not query.strip():
        return []

    bm25_results = get_bm25().search(query, top_k)
    vector_results = get_vector().search(query, top_k)

    combined = {}

    for result in bm25_results:
        combined[result.doc_id] = {
            "doc_id": result.doc_id,
            "title": result.document.get("title", ""),
            "bm25_score": result.score,
            "vector_score": 0,
        }

    for result in vector_results:
        document = combined.setdefault(
            result.doc_id,
            {
                "doc_id": result.doc_id,
                "title": result.title,
                "bm25_score": 0,
                "vector_score": 0,
            },
        )
        document["vector_score"] = result.score

    return list(combined.values())
