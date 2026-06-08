from app.rag.index import reset_index
from app.rag.loader import reset_chunks
from app.rag.retriever import search_knowledge


def setup_function():
    reset_chunks()
    reset_index()


def test_search_knowledge_returns_hits():
    hits = search_knowledge("сколько дней на возврат товара")
    assert hits
    assert any("14" in hit["text"] for hit in hits)


def test_search_knowledge_empty_query():
    assert search_knowledge("  ") == []
