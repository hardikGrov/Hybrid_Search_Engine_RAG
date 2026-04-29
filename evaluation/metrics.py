import math


def mean_reciprocal_rank(results, qrels):
    reciprocal_ranks = []

    for query_id, relevant_doc_ids in qrels.items():
        relevant_doc_ids = set(relevant_doc_ids)
        reciprocal_rank = 0

        for rank, doc_id in enumerate(results.get(query_id, []), start=1):
            if doc_id in relevant_doc_ids:
                reciprocal_rank = 1 / rank
                break

        reciprocal_ranks.append(reciprocal_rank)

    if not reciprocal_ranks:
        return 0

    return sum(reciprocal_ranks) / len(reciprocal_ranks)


def ndcg_at_k(results, qrels, k):
    if k <= 0:
        return 0

    ndcg_scores = []

    for query_id, relevant_doc_ids in qrels.items():
        relevant_doc_ids = set(relevant_doc_ids)
        ranked_doc_ids = results.get(query_id, [])[:k]

        dcg = sum(
            1 / math.log2(rank + 1)
            for rank, doc_id in enumerate(ranked_doc_ids, start=1)
            if doc_id in relevant_doc_ids
        )

        ideal_relevant_count = min(len(relevant_doc_ids), k)
        idcg = sum(1 / math.log2(rank + 1) for rank in range(1, ideal_relevant_count + 1))

        if idcg == 0:
            ndcg_scores.append(0)
        else:
            ndcg_scores.append(dcg / idcg)

    if not ndcg_scores:
        return 0

    return sum(ndcg_scores) / len(ndcg_scores)
