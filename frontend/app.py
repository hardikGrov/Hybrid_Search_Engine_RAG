import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st

API_URL = "http://localhost:8000/search"
RESULT_COLUMNS = ["doc_id", "title", "bm25_score", "vector_score", "hybrid_score"]


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


st.set_page_config(page_title="Hybrid Search", layout="wide")
st.title("Hybrid Search")

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
            results = search_backend(query, int(top_k), alpha)
        except HTTPError as error:
            st.error(f"Search request failed: HTTP {error.code}")
        except URLError:
            st.error("Could not connect to the backend API at http://localhost:8000.")
        except TimeoutError:
            st.error("Search request timed out.")
        else:
            rows = [{column: result.get(column, "") for column in RESULT_COLUMNS} for result in results]
            st.dataframe(rows, use_container_width=True, hide_index=True)
