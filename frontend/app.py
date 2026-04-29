import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st

API_URL = "http://localhost:8000/search"
RESULT_COLUMNS = [
    "rank",
    "doc_id",
    "title",
    "bm25_score",
    "vector_score",
    "hybrid_score",
    "hybrid_rank",
    "rank_delta",
]


def search_backend(query: str, top_k: int, alpha: float):
    payload = json.dumps(
        {
            "query": query,
            "top_k": top_k,
            "alpha": alpha,
        }
    ).encode("utf-8")
    request = Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8")).get("results", [])


def ranked_rows(results, hybrid_ranks=None):
    rows = []
    hybrid_ranks = hybrid_ranks or {}

    for rank, result in enumerate(results, start=1):
        hybrid_rank = hybrid_ranks.get(result.get("doc_id"))
        rank_delta = "" if hybrid_rank is None else hybrid_rank - rank
        rows.append(
            {
                "rank": rank,
                "doc_id": result.get("doc_id", ""),
                "title": result.get("title", ""),
                "bm25_score": result.get("bm25_score", ""),
                "vector_score": result.get("vector_score", ""),
                "hybrid_score": result.get("hybrid_score", ""),
                "hybrid_rank": "" if hybrid_rank is None else hybrid_rank,
                "rank_delta": rank_delta,
            }
        )

    return rows


def render_results(label, results, hybrid_ranks=None):
    st.subheader(label)
    rows = ranked_rows(results, hybrid_ranks=hybrid_ranks)
    changed_count = sum(1 for row in rows if row["rank_delta"] not in ("", 0))
    deltas = [
    abs(row["rank_delta"])
    for row in rows
    if row["rank_delta"] not in ("", 0)
]

    avg_shift = round(sum(deltas) / len(deltas), 2) if deltas else 0.0

    st.metric("Avg rank shift vs Hybrid", avg_shift)
    st.dataframe(
        [{column: row[column] for column in RESULT_COLUMNS} for row in rows],
        use_container_width=True,
        hide_index=True,
    )


st.set_page_config(page_title="Hybrid Search", layout="wide")
st.title("Hybrid Search")
st.caption(
    "Hybrid ranking combines BM25 (exact match) and vector search (semantic similarity). "
    "Alpha controls the balance: alpha=1 → BM25, alpha=0 → Vector."
)

with st.form("search-form"):
    query = st.text_input("Query")
    alpha = st.slider("Alpha", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
    top_k = st.number_input("Top K", min_value=1, max_value=50, value=10, step=1)
    submitted = st.form_submit_button("Search")

if submitted:
    if not query.strip():
        st.warning("Enter a query to search.")
    else:
        try:
            top_k = int(top_k)
            start = time.time()
            bm25_results = search_backend(query, top_k, alpha=1.0)
            vector_results = search_backend(query, top_k, alpha=0.0)
            hybrid_results = search_backend(query, top_k, alpha=alpha)
            latency_ms = int((time.time() - start) * 1000)
        except HTTPError as error:
            st.error(f"Search request failed: HTTP {error.code}")
        except URLError:
            st.error("Could not connect to the backend API at http://localhost:8000.")
        except TimeoutError:
            st.error("Search request timed out.")
        else:
            st.caption(f"Latency: {latency_ms} ms")
            hybrid_ranks = {
                result.get("doc_id"): rank for rank, result in enumerate(hybrid_results, start=1)
            }
            st.caption("Rank delta compares each section's rank with the Hybrid rank.")

            bm25_column, vector_column, hybrid_column = st.columns(3)
            with bm25_column:
                render_results("Lexical (BM25)", bm25_results, hybrid_ranks=hybrid_ranks)
            with vector_column:
                render_results("Semantic (Vector)", vector_results, hybrid_ranks=hybrid_ranks)
            with hybrid_column:
                render_results("Hybrid", hybrid_results, hybrid_ranks=hybrid_ranks)
