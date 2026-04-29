import importlib
import sys
import types

import pytest


class FakeArray(list):
    @property
    def shape(self):
        rows = len(self)
        columns = len(self[0]) if rows else 0
        return rows, columns


class FakeIndexFlatIP:
    def __init__(self, dimension):
        self.dimension = dimension
        self.embeddings = None

    def add(self, embeddings):
        self.embeddings = embeddings

    def search(self, query_embedding, top_k):
        query = query_embedding[0]
        scored_indices = [
            (
                sum(query_value * doc_value for query_value, doc_value in zip(query, embedding)),
                index,
            )
            for index, embedding in enumerate(self.embeddings)
        ]
        scored_indices.sort(reverse=True)
        top_results = scored_indices[:top_k]
        return [[score for score, _ in top_results]], [[index for _, index in top_results]]


class FakeSentenceTransformer:
    instances = []

    def __init__(self, model_name, device):
        self.model_name = model_name
        self.device = device
        self.encode_calls = []
        FakeSentenceTransformer.instances.append(self)

    def encode(
        self,
        texts,
        convert_to_numpy,
        normalize_embeddings,
        show_progress_bar,
        batch_size,
    ):
        self.encode_calls.append(
            {
                "texts": texts,
                "convert_to_numpy": convert_to_numpy,
                "normalize_embeddings": normalize_embeddings,
                "show_progress_bar": show_progress_bar,
                "batch_size": batch_size,
            }
        )
        return [embedding_for_text(text) for text in texts]


def embedding_for_text(text):
    normalized = text.lower()
    if "apple" in normalized:
        return [1.0, 0.0]
    if "banana" in normalized:
        return [0.0, 1.0]
    return [0.5, 0.5]


@pytest.fixture
def vector_module(monkeypatch):
    FakeSentenceTransformer.instances = []

    fake_numpy = types.ModuleType("numpy")
    fake_numpy.ndarray = FakeArray
    fake_numpy.asarray = lambda values, dtype=None: FakeArray([list(value) for value in values])

    fake_faiss = types.ModuleType("faiss")
    fake_faiss.IndexFlatIP = FakeIndexFlatIP

    fake_sentence_transformers = types.ModuleType("sentence_transformers")
    fake_sentence_transformers.SentenceTransformer = FakeSentenceTransformer

    fake_torch = types.ModuleType("torch")
    fake_torch.thread_counts = []
    fake_torch.set_num_threads = lambda thread_count: fake_torch.thread_counts.append(thread_count)

    monkeypatch.setitem(sys.modules, "numpy", fake_numpy)
    monkeypatch.setitem(sys.modules, "faiss", fake_faiss)
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_sentence_transformers)
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    sys.modules.pop("hybrid_search.index.vector", None)

    module = importlib.import_module("hybrid_search.index.vector")
    yield module
    sys.modules.pop("hybrid_search.index.vector", None)


def test_constructor_loads_sentence_transformer_on_cpu(vector_module):
    index = vector_module.VectorIndex("test-model")

    assert index.model.model_name == "test-model"
    assert index.model.device == "cpu"
    assert index.documents == []
    assert index.index is None


def test_import_limits_torch_to_single_thread(vector_module):
    assert vector_module.torch.thread_counts == [1]


def test_fit_builds_faiss_index_from_document_text(vector_module):
    documents = [
        {"doc_id": "doc_0", "title": "Apple", "text": "apple document"},
        {"doc_id": "doc_1", "title": "Banana", "text": "banana document"},
    ]

    index = vector_module.VectorIndex("test-model").fit(documents)

    assert index.documents == documents
    assert isinstance(index.index, FakeIndexFlatIP)
    assert index.index.dimension == 2
    assert index.index.embeddings == [[1.0, 0.0], [0.0, 1.0]]
    assert index.model.encode_calls[0] == {
        "texts": ["apple document", "banana document"],
        "convert_to_numpy": True,
        "normalize_embeddings": True,
        "show_progress_bar": False,
        "batch_size": 16,
    }


def test_search_returns_ranked_vector_results(vector_module):
    documents = [
        {"doc_id": "apple-doc", "title": "Apple", "text": "apple document"},
        {"doc_id": "banana-doc", "title": "Banana", "text": "banana document"},
        {"doc_id": "mixed-doc", "title": "Mixed", "text": "mixed document"},
    ]

    results = vector_module.VectorIndex("test-model").fit(documents).search("apple query", top_k=2)

    assert [result.doc_id for result in results] == ["apple-doc", "mixed-doc"]
    assert [result.title for result in results] == ["Apple", "Mixed"]
    assert all(isinstance(result, vector_module.VectorSearchResult) for result in results)
    assert results[0].score > results[1].score
    assert results[0].document == documents[0]


def test_search_limits_top_k_to_document_count(vector_module):
    documents = [{"doc_id": "doc_0", "title": "Apple", "text": "apple document"}]

    results = vector_module.VectorIndex("test-model").fit(documents).search("apple", top_k=10)

    assert len(results) == 1
    assert results[0].doc_id == "doc_0"


def test_search_returns_empty_list_for_blank_query(vector_module):
    documents = [{"doc_id": "doc_0", "title": "Apple", "text": "apple document"}]

    results = vector_module.VectorIndex("test-model").fit(documents).search("   ")

    assert results == []


def test_fit_rejects_empty_document_collection(vector_module):
    with pytest.raises(ValueError, match="at least one document"):
        vector_module.VectorIndex("test-model").fit([])


def test_search_requires_fit(vector_module):
    with pytest.raises(ValueError, match="fit before searching"):
        vector_module.VectorIndex("test-model").search("apple")


def test_search_rejects_non_positive_top_k(vector_module):
    documents = [{"doc_id": "doc_0", "title": "Apple", "text": "apple document"}]
    index = vector_module.VectorIndex("test-model").fit(documents)

    with pytest.raises(ValueError, match="top_k"):
        index.search("apple", top_k=0)
