from app.rag.embeddings import embed_texts, use_openai_embeddings
from app.rag.loader import load_chunks

_index: list[dict] | None = None
_index_mode: str | None = None


def reset_index() -> None:
    global _index, _index_mode
    _index = None
    _index_mode = None


def warm_index() -> int:
    """Build in-memory vector index. Returns chunk count."""
    global _index, _index_mode
    chunks = load_chunks()
    if not chunks:
        _index = []
        _index_mode = "empty"
        return 0

    texts = [f"{chunk['title']}\n{chunk['text']}" for chunk in chunks]
    vectors = embed_texts(texts)
    _index = [
        {
            "chunk": chunk,
            "vector": vector,
        }
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    _index_mode = "openai" if use_openai_embeddings() else "mock"
    return len(_index)


def get_index() -> list[dict]:
    if _index is None:
        warm_index()
    return _index or []


def index_mode() -> str:
    if _index_mode is None:
        warm_index()
    return _index_mode or "empty"


def index_size() -> int:
    return len(get_index())
