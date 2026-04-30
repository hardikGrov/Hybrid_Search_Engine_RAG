import sqlite3
from pathlib import Path


DB_PATH = Path("data/query_logs.db")


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT,
                query TEXT,
                latency_ms INTEGER,
                top_k INTEGER,
                alpha REAL,
                result_count INTEGER,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def get_metrics_stats() -> tuple[int, float]:
    """Return (total row count, average latency_ms) from query_logs."""
    if not DB_PATH.exists():
        return 0, 0.0
    try:
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT COUNT(*), AVG(latency_ms) FROM query_logs"
            ).fetchone()
    except sqlite3.Error:
        return 0, 0.0
    total = int(row[0] or 0)
    avg = row[1]
    if avg is None:
        return total, 0.0
    return total, float(avg)


def insert_log(data: dict) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO query_logs (
                request_id,
                query,
                latency_ms,
                top_k,
                alpha,
                result_count,
                error
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("request_id"),
                data.get("query"),
                data.get("latency_ms"),
                data.get("top_k"),
                data.get("alpha"),
                data.get("result_count"),
                data.get("error"),
            ),
        )
        conn.commit()
