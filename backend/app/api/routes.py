from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from backend.app.services.search_service import search_documents

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResponse(BaseModel):
    results: List[dict]


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest):
    results = search_documents(payload.query, payload.top_k)
    return {"results": results}