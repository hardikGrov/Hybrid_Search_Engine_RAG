import math
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


TOKEN_PATTERN = re.compile(r"\b\w+\b")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


@dataclass(frozen=True)
class BM25Result:
    doc_id: str
    score: float
    document: dict[str, Any]


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        if k1 <= 0:
            raise ValueError("k1 must be greater than 0.")
        if not 0 <= b <= 1:
            raise ValueError("b must be between 0 and 1.")

        self.k1 = k1
        self.b = b
        self.documents: list[dict[str, Any]] = []
        self.term_frequencies: list[Counter[str]] = []
        self.document_frequencies: Counter[str] = Counter()
        self.document_lengths: list[int] = []
        self.average_document_length = 0.0

    def fit(self, documents: Iterable[dict[str, Any]]) -> "BM25Index":
        self.documents = list(documents)
        if not self.documents:
            raise ValueError("BM25Index requires at least one document.")

        self.term_frequencies = []
        self.document_frequencies = Counter()
        self.document_lengths = []

        for document in self.documents:
            tokens = tokenize(str(document.get("text", "")))
            term_frequency = Counter(tokens)
            self.term_frequencies.append(term_frequency)
            self.document_frequencies.update(term_frequency.keys())
            self.document_lengths.append(len(tokens))

        self.average_document_length = sum(self.document_lengths) / len(self.document_lengths)
        return self

    def score(self, query: str, document_index: int) -> float:
        if not self.documents:
            raise ValueError("BM25Index must be fit before scoring.")
        if document_index < 0 or document_index >= len(self.documents):
            raise IndexError("document_index is out of range.")

        query_terms = tokenize(query)
        if not query_terms:
            return 0.0

        score = 0.0
        total_documents = len(self.documents)
        document_length = self.document_lengths[document_index]
        term_frequency = self.term_frequencies[document_index]

        for term in query_terms:
            frequency = term_frequency.get(term, 0)
            if frequency == 0:
                continue

            matching_documents = self.document_frequencies[term]
            idf = math.log(
                1 + (total_documents - matching_documents + 0.5) / (matching_documents + 0.5)
            )
            length_norm = 1 - self.b
            if self.average_document_length:
                length_norm += self.b * (document_length / self.average_document_length)

            numerator = frequency * (self.k1 + 1)
            denominator = frequency + self.k1 * length_norm
            score += idf * (numerator / denominator)

        return score

    def search(self, query: str, top_k: int = 5) -> list[BM25Result]:
        if not self.documents:
            raise ValueError("BM25Index must be fit before searching.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        results = [
            BM25Result(
                doc_id=str(document.get("doc_id", index)),
                score=self.score(query, index),
                document=document,
            )
            for index, document in enumerate(self.documents)
        ]
        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_k]
