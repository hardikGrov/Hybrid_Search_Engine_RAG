import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st

API_URL = "http://localhost:8000/search"


def search_backend(query: str, top_k: int, alpha: float):
    payload = json.dumps(
        {"query": query, "top_k": top_k, "alpha": alpha}
    ).encode("utf-8")

    request = Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8")).get("results", [])


def score_text(value):
    return f"{value:.4f}" if isinstance(value, (int, float)) else "-"


def render_results(label, results, hybrid_ranks=None):
    st.subheader(label)
    hybrid_ranks = hybrid_ranks or {}

    if not results:
        st.info("No results.")
        return

    # Avg rank shift
    deltas = []
    for rank, r in enumerate(results, start=1):
        h_rank = hybrid_ranks.get(r.get("doc_id"))
        if h_rank and h_rank != rank:
            deltas.append(abs(h_rank - rank))

    avg_shift = round(sum(deltas) / len(deltas), 2) if deltas else 0.0
    st.metric("Avg Rank Shift vs Hybrid", avg_shift)

    for rank, result in enumerate(results, start=1):
        doc_id = result.get("doc_id", "")
        title = result.get("title", "")

        h_rank = hybrid_ranks.get(doc_id)
        delta = f"(Δ {rank - h_rank:+})" if h_rank else ""

        with st.expander(
            f"#{rank} {doc_id} {delta} | {title}",
            expanded=(rank == 1),
        ):
            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown("**BM25**")
                st.write(score_text(result.get("bm25_score")))

            with c2:
                st.markdown("**Vector**")
                st.write(score_text(result.get("vector_score")))

            with c3:
                st.markdown("**Hybrid**")
                st.write(score_text(result.get("hybrid_score")))


# ---------------- UI ---------------- #

st.title("🔍 Hybrid Search Engine")

st.caption(
    "Compare BM25 (keyword), Vector (semantic), and Hybrid ranking.\n"
    "Hybrid = α * BM25 + (1-α) * Vector"
)

st.subheader("Query")

query = st.text_input(
    "Enter search query",
    placeholder="e.g. What is the capital of France?",
)

col1, col2 = st.columns(2)

with col1:
    alpha = st.slider(
        "Alpha (BM25 ↔ Vector)",
        0.0,
        1.0,
        0.5,
        step=0.05,
        help="0 = semantic only, 1 = keyword only",
    )
    st.caption(
        f"Mode: {'Balanced' if alpha==0.5 else ('Keyword-heavy' if alpha>0.5 else 'Semantic-heavy')}"
    )

with col2:
    top_k = st.number_input("Top K results", 1, 50, 10)

search_clicked = st.button("🚀 Search", use_container_width=True)


# ---------------- Search ---------------- #

if search_clicked:
    if not query.strip():
        st.warning("Please enter a query.")
    else:
        try:
            start = time.time()

            bm25_results = search_backend(query, int(top_k), alpha=1.0)
            vector_results = search_backend(query, int(top_k), alpha=0.0)
            hybrid_results = search_backend(query, int(top_k), alpha=alpha)

            latency = int((time.time() - start) * 1000)

        except HTTPError as e:
            st.error(f"HTTP Error: {e.code}")
        except URLError:
            st.error("Backend not reachable.")
        except TimeoutError:
            st.error("Request timed out.")

        else:
            st.divider()
            st.subheader("Results")

            c1, c2 = st.columns(2)
            c1.metric("Latency", f"{latency} ms")
            c2.metric("Results Returned", len(hybrid_results))

            st.caption("Δ shows how rank differs from Hybrid ranking")

            hybrid_ranks = {
                r.get("doc_id"): i for i, r in enumerate(hybrid_results, start=1)
            }

            col1, col2, col3 = st.columns(3)

            with col1:
                render_results("BM25 (Keyword)", bm25_results, hybrid_ranks)

            with col2:
                render_results("Vector (Semantic)", vector_results, hybrid_ranks)

            with col3:
                render_results("Hybrid (Final)", hybrid_results, hybrid_ranks)