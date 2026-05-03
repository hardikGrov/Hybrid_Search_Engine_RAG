import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path("data/query_logs.db")


def load_logs() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()

    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(
                """
                SELECT
                    request_id,
                    query,
                    latency_ms,
                    result_count,
                    created_at
                FROM query_logs
                ORDER BY created_at ASC
                """,
                conn,
            )
    except sqlite3.Error:
        return pd.DataFrame()

    if df.empty:
        return df

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.dropna(subset=["created_at"])
    return df


st.title("KPI")
st.caption("KPI dashboard from SQLite query logs.")

if st.button("Refresh", type="primary"):
    st.rerun()

logs_df = load_logs()

if logs_df.empty:
    st.warning("No logs found in data/query_logs.db yet.")
else:
    # Top metrics
    latency_series = pd.to_numeric(logs_df["latency_ms"], errors="coerce").dropna()
    p50_latency = float(latency_series.quantile(0.50)) if not latency_series.empty else 0.0
    p95_latency = float(latency_series.quantile(0.95)) if not latency_series.empty else 0.0
    total_requests = int(len(logs_df))

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("p50 latency (ms)", f"{p50_latency:.2f}")
    with metric_col2:
        st.metric("p95 latency (ms)", f"{p95_latency:.2f}")
    with metric_col3:
        st.metric("Total requests", total_requests)

    st.subheader("Request volume over time")
    volume_df = (
        logs_df.assign(time_bin=logs_df["created_at"].dt.floor("min"))
        .groupby("time_bin", as_index=True)["request_id"]
        .count()
        .rename("requests")
        .to_frame()
    )
    st.line_chart(volume_df)

    st.subheader("Latency over time")
    latency_over_time_df = (
        logs_df.assign(
            time_bin=logs_df["created_at"].dt.floor("min"),
            latency_ms=pd.to_numeric(logs_df["latency_ms"], errors="coerce"),
        )
        .dropna(subset=["latency_ms"])
        .groupby("time_bin", as_index=True)["latency_ms"]
        .mean()
        .rename("avg_latency_ms")
        .to_frame()
    )
    st.line_chart(latency_over_time_df)

    st.subheader("Top queries")
    top_queries_df = (
        logs_df.assign(query=logs_df["query"].fillna("").astype(str).str.strip())
        .loc[lambda df: df["query"] != ""]
        .groupby("query", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=False)
        .head(10)
    )
    if top_queries_df.empty:
        st.info("No query data available.")
    else:
        st.bar_chart(top_queries_df.set_index("query"))
        st.dataframe(top_queries_df, use_container_width=True, hide_index=True)

    st.subheader("Zero-result queries")
    zero_result_df = (
        logs_df.assign(
            result_count=pd.to_numeric(logs_df["result_count"], errors="coerce").fillna(0),
            query=logs_df["query"].fillna("").astype(str).str.strip(),
        )
        .loc[lambda df: (df["result_count"] <= 0) & (df["query"] != "")]
        .groupby("query", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=False)
    )
    if zero_result_df.empty:
        st.info("No zero-result queries found.")
    else:
        st.dataframe(zero_result_df, use_container_width=True, hide_index=True)
