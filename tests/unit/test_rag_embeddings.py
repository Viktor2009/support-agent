from app.config import settings
from app.rag.index import index_mode, reset_index, warm_index
from app.rag.loader import reset_chunks
from app.rag.retriever import resolve_rag_mode, search_embedding, search_keyword, search_knowledge
from app.rag.vectors import cosine_similarity, mock_embedding


def setup_function():
    reset_chunks()
    reset_index()
    warm_index()


def test_mock_embedding_is_normalized():
    vector = mock_embedding("возврат товара политика")
    norm = sum(component * component for component in vector) ** 0.5
    assert abs(norm - 1.0) < 0.01


def test_cosine_similarity_identical_vectors():
    vector = mock_embedding("доставка заказ")
    assert cosine_similarity(vector, vector) > 0.99


def test_search_embedding_returns_method(monkeypatch):
    monkeypatch.setattr(settings, "mock_llm", True)
    monkeypatch.setattr(settings, "rag_use_mock_embeddings", True)
    hits = search_embedding("возврат товара сколько дней")
    assert hits
    assert hits[0]["retrieval_method"] == "embedding"
    assert any("14" in hit["text"] for hit in hits)


def test_search_knowledge_embedding_with_keyword_fallback(monkeypatch):
    monkeypatch.setattr(settings, "mock_llm", True)
    monkeypatch.setattr(settings, "rag_mode", "embedding")
    hits = search_knowledge("сколько дней на возврат товара")
    assert hits
    assert any("14" in hit["text"] for hit in hits)


def test_search_keyword_still_works():
    hits = search_keyword("сколько дней на возврат товара")
    assert hits
    assert hits[0]["retrieval_method"] == "keyword"


def test_resolve_rag_mode_mock_embedding(monkeypatch):
    monkeypatch.setattr(settings, "mock_llm", True)
    monkeypatch.setattr(settings, "rag_use_mock_embeddings", True)
    assert resolve_rag_mode() == "embedding"


def test_resolve_rag_mode_keyword_only(monkeypatch):
    monkeypatch.setattr(settings, "mock_llm", True)
    monkeypatch.setattr(settings, "rag_use_mock_embeddings", False)
    monkeypatch.setattr(settings, "rag_mode", "auto")
    assert resolve_rag_mode() == "keyword"


def test_index_mode_after_warm():
    assert index_mode() in ("mock", "openai", "empty")
    assert warm_index() >= 4
