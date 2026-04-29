from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
import time
import uuid
from typing import List

from backend.app.db.sqlite import get_metrics_stats, insert_log
from backend.app.services.search_service import search_documents
from backend.app.utils.logger import log_request

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=50)
    alpha: float = Field(0.5, ge=0.0, le=1.0)


class SearchResponse(BaseModel):
    results: List[dict]


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/metrics", response_class=PlainTextResponse)
def metrics():
    total, avg_ms = get_metrics_stats()
    return f"requests_total {total}\navg_latency_ms {avg_ms:g}\n"


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()
    try:
        results = search_documents(payload.query, payload.top_k, alpha=payload.alpha)
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        log_data = {
            "request_id": request_id,
            "query": payload.query,
            "latency_ms": latency_ms,
            "top_k": payload.top_k,
            "alpha": payload.alpha,
            "result_count": len(results),
            "error": None,
        }
        try:
            log_request(log_data)
            insert_log(log_data)
        except Exception:
            pass
        return {"results": results}
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        error = str(exc)
        log_data = {
            "request_id": request_id,
            "query": payload.query,
            "latency_ms": latency_ms,
            "top_k": payload.top_k,
            "alpha": payload.alpha,
            "result_count": 0,
            "error": error,
        }
        try:
            log_request(log_data)
            insert_log(log_data)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=error) from exc
