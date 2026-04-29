import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.search_service import search_documents
from evaluation.metrics import mean_reciprocal_rank, ndcg_at_k

EVALUATION_DIR = Path(__file__).resolve().parent
QUERIES_PATH = EVALUATION_DIR / "queries.json"
QRELS_PATH = EVALUATION_DIR / "qrels.json"


def load_queries():
    return json.loads(QUERIES_PATH.read_text())


def load_qrels():
    return json.loads(QRELS_PATH.read_text())


def run_searches(queries, top_k, alpha):
    ranked_results = {}

    for query in queries:
        results = search_documents(query["query"], top_k=top_k, alpha=alpha)
        ranked_results[query["id"]] = [result["doc_id"] for result in results]

    return ranked_results


def evaluate_run(name, queries, qrels, top_k, alpha):
    ranked_results = run_searches(queries, top_k=top_k, alpha=alpha)
    mrr = mean_reciprocal_rank(ranked_results, qrels)
    ndcg = ndcg_at_k(ranked_results, qrels, k=10)

    print(f"{name}")
    print(f"MRR: {mrr:.4f}")
    print(f"nDCG@10: {ndcg:.4f}")
    print()


def main():
    top_k = 10
    queries = load_queries()
    qrels = load_qrels()

    evaluate_run("BM25 only", queries, qrels, top_k=top_k, alpha=1.0)
    evaluate_run("Vector only", queries, qrels, top_k=top_k, alpha=0.0)
    evaluate_run("Hybrid", queries, qrels, top_k=top_k, alpha=0.5)


if __name__ == "__main__":
    main()
