import sqlite3
from datetime import datetime, timedelta, timezone
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
                    error,
                    created_at
                FROM query_logs
                ORDER BY created_at DESC
                """,
                conn,
            )
    except sqlite3.Error:
        return pd.DataFrame()

    if df.empty:
        return df

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    return df.dropna(subset=["created_at"])


st.title("Debug")
st.caption("Debug view from SQLite request logs.")

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    time_range = st.selectbox(
    "Time range",
    ["Last 1h", "Last 24h", "Last 7d", "Last 30d"],
    index=0,
)
with filter_col2:
    error_only = st.checkbox("Error only", value=False)

if st.button("Refresh", type="primary"):
    st.rerun()

logs_df = load_logs()

if logs_df.empty:
    st.warning("No logs found in data/query_logs.db.")
else:
    logs_df["created_at"] = logs_df["created_at"].dt.tz_localize(None)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if time_range == "Last 1h":
        cutoff = now - timedelta(hours=1)
    elif time_range == "Last 24h":
        cutoff = now - timedelta(hours=24)
    elif time_range == "Last 7d":
        cutoff = now - timedelta(days=7)
    elif time_range == "Last 30d":
        cutoff = now - timedelta(days=30)

    filtered = logs_df[logs_df["created_at"] >= cutoff].copy()
    if error_only:
        error_series = filtered["error"].fillna("").astype(str).str.strip()
        filtered = filtered[error_series != ""]

    filtered = filtered.sort_values("created_at", ascending=False)
    display_df = filtered[["request_id", "query", "latency_ms", "error"]]

    st.dataframe(display_df, use_container_width=True, hide_index=True)
