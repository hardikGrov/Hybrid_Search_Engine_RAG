import json
from pathlib import Path
from hybrid_search.index.bm25 import BM25Index

DATA_PATH = Path("data/processed/docs.jsonl")

_docs = None
_bm25 = None


def get_bm25():
    global _docs, _bm25

    if _bm25 is not None:
        return _bm25

    if not DATA_PATH.exists():
        raise RuntimeError("Processed data not found")

    _docs = []
    with open(DATA_PATH) as f:
        for line in f:
            _docs.append(json.loads(line))

    _bm25 = BM25Index().fit(_docs)
    return _bm25


def search_documents(query: str, top_k: int):
    if not query.strip():
        return []

    index = get_bm25()
    results = index.search(query, top_k)

    return [
        {
            "doc_id": r.doc_id,
            "title": r.document.get("title", ""),
            "bm25_score": r.score,
        }
        for r in results
    ]