from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

import torch
torch.set_num_threads(1)


os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"


@dataclass(frozen=True)
class VectorSearchResult:
    doc_id: str
    title: str
    score: float
    document: dict[str, Any]


class VectorIndex:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model = SentenceTransformer(model_name, device="cpu")
        self.documents: list[dict[str, Any]] = []
        self.index: faiss.IndexFlatIP | None = None

    def fit(self, documents: Iterable[dict[str, Any]]) -> "VectorIndex":
        self.documents = list(documents)
        if not self.documents:
            raise ValueError("VectorIndex requires at least one document.")

        texts = [str(document.get("text", "")) for document in self.documents]
        embeddings = self._embed(texts)

        self.index = faiss.IndexFlatIP(embeddings.shape[1])
        self.index.add(embeddings)
        return self

    def search(self, query: str, top_k: int = 5) -> list[VectorSearchResult]:
        if self.index is None:
            raise ValueError("VectorIndex must be fit before searching.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")
        if not query.strip():
            return []

        query_embedding = self._embed([query])
        scores, indices = self.index.search(query_embedding, min(top_k, len(self.documents)))

        results = []
        for score, index in zip(scores[0], indices[0], strict=True):
            if index == -1:
                continue

            document = self.documents[index]
            results.append(
                VectorSearchResult(
                    doc_id=str(document["doc_id"]),
                    title=str(document["title"]),
                    score=float(score),
                    document=document,
                )
            )

        return results

    def _embed(self, texts: list[str]) -> np.ndarray:
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=16,
        )
        return np.asarray(embeddings, dtype="float32")
