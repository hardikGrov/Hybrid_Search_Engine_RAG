# Codex / Cursor development log

## Introduction

This document records how **Codex** and **Cursor** were used to plan, implement, and iterate on the hybrid search project: prompts sent to the assistant, what shipped as a result, and how those changes landed in git.

Use it as a lightweight narrative alongside commits and PRs.

---

## Raw Prompt Export

This section records the visible prompts sent to Codex during the hybrid search implementation session.

### Prompt 1

```text
ERROR tests/test_vector.py::test_constructor_loads_sentence_transformer_on_cpu - AttributeError: module 'numpy' has no attribute 'bool_'
while running vector_test
```

### Prompt 2

```text
these changes are needed to run vector search locally
```

### Prompt 3

```text
update and fix vector_search tests to make sure single thread and fix batch size
```

### Prompt 4

```text
Update search_documents() in backend/app/services/search_service.py.

Requirements:
- Call both BM25 and VectorIndex
- Combine results into a dictionary keyed by doc_id

Each doc should contain:
{
  "doc_id": ...,
  "title": ...,
  "bm25_score": ...,
  "vector_score": ...
}
- Do NOT normalize yet
- Do NOT combine scores yet
```

### Prompt 5

```text
In backend/app/services/search_service.py, create a helper function normalize_scores(scores: list[float]).

Requirements:
Use min-max normalization:
    normalized = (score - min) / (max - min)
Do NOT modify existing search logic
```

### Prompt 6

```text
Update search_documents() in search_service.py.

Requirements:
- After merging results, extract:
    - all bm25_score values
    - all vector_score values
- Normalize both lists independently using normalize_scores()

Then update each document to include:
    "bm25_norm": ...
    "vector_norm": ...

Do NOT combine scores yet.
Do NOT change return format yet.
```

### Prompt 7

```text
Update search_documents().

Requirements:
- Add parameter alpha (default = 0.5)
- Compute hybrid_score per document:

    hybrid_score = alpha * bm25_norm + (1 - alpha) * vector_norm

- Add "hybrid_score" to each result

Do NOT change sorting yet.
```

### Prompt 8

```text
Update search_documents().

Requirements:
- Sort results by hybrid_score descending
- Apply top_k AFTER sorting
- Ensure deterministic ordering:
    tie-break using doc_id

Return final top_k results only
```

### Prompt 9

```text
Update search_documents() output.

Requirements:
- Return only:
    doc_id
    title
    bm25_score
    vector_score
    hybrid_score
- Remove bm25_norm and vector_norm from final response
- Keep them internal only
```

### Prompt 10

```text
Create evaluation/queries.json.

Requirements:
- Add at least 25 queries
- Use realistic queries from the dataset
- Each query should have:
    id
    query
```

### Prompt 11

```text
Create evaluation/qrels.json.

Requirements:
- Map query_id -> list of relevant doc_ids
- Use your dataset knowledge to label relevance
- Keep it simple (binary relevance)

Example:
{
  "q1": ["doc_195", "doc_191"],
  "q2": ["doc_195"]
}
```

### Prompt 12

```text
Create evaluation/metrics.py.

Implement function mean_reciprocal_rank(results, qrels).

Requirements:
- For each query:
    find rank of first relevant doc
    compute reciprocal rank = 1 / rank
- Return average across all queries

Edge cases:
- no relevant doc found -> score = 0
```

### Prompt 13

```text
In metrics.py implement ndcg_at_k(results, qrels, k).

Requirements:
- Compute DCG:
    sum relevance / log2(rank+1)
- Compute IDCG (ideal ranking)
- Return DCG / IDCG

Constraints:
- relevance is binary (0 or 1)
- return value between 0 and 1
```

### Prompt 14

```text
Create evaluation/run_eval.py.

Requirements:
- Load queries.json and qrels.json
- For each query:
    call search_documents(query, top_k)
- Store ranked doc_ids

Run evaluation for BM25 only, Vector only, Hybrid

Print MRR and nDCG@10
```

### Prompt 15

```text
generate 10 harder and more ambiguous queries for evals, update last 10 queries in queries and qrels accordingly
```

### Prompt 16

```text
Create frontend/app.py Streamlit dashboard.

Requirements:
- Input box for query
- Slider for alpha from 0 to 1
- top_k selector
- Call search API
- Display doc_id, title, bm25_score, vector_score, hybrid_score results in table
```

### Prompt 17

```text
Enhance Streamlit UI.

Requirements:
- Show 3 sections:
    1. BM25 results
    2. Vector results
    3. Hybrid results

Highlight ranking differences and show rank index

```
### Prompt 19

```text
Enhance Streamlit tables.

Requirements:
- Add color coding for rank_delta:
    - positive (improved rank) -> green
    - negative (worse rank) -> red
    - 0 -> neutral

- Use conditional formatting for table cells
```

### Prompt 20

```text
Enhance Streamlit tables.

Requirements:
- Add color coding for rank_delta positive (improved rank) -> green, negative (worse rank) -> red, 0 -> neutral

- Use conditional formatting for table cells
```

### Prompt 21

```text
update readme to include summary, overview, architecture, components, eval, results,project running steps.
```

### Prompt 22

```text
do an export of all codex prompts to docs/codex_log.md
```
