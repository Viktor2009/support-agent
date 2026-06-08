from app.config import settings
from app.rag.embeddings import use_openai_embeddings
from app.rag.index import get_index
from app.rag.loader import load_chunks
from app.rag.vectors import cosine_similarity, tokenize


def _tokenize(text: str) -> set[str]:
    return set(tokenize(text))


def _chunk_hit(chunk: dict, score: float, method: str) -> dict:
    return {
        "source_type": "knowledge",
        "source_id": chunk["id"],
        "title": chunk["title"],
        "text": chunk["text"],
        "score": round(score, 3),
        "retrieval_method": method,
    }


def search_keyword(
    query: str,
    top_k: int = 3,
    min_score: float = 0.15,
) -> list[dict]:
    """Keyword overlap retriever (works offline without embeddings)."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    scored: list[tuple[float, dict]] = []
    for chunk in load_chunks():
        text_tokens = _tokenize(chunk["text"] + " " + chunk["title"])
        if not text_tokens:
            continue
        overlap = query_tokens & text_tokens
        score = len(overlap) / len(query_tokens)
        if score >= min_score:
            scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [_chunk_hit(chunk, score, "keyword") for score, chunk in scored[:top_k]]


def search_embedding(
    query: str,
    top_k: int = 3,
    min_score: float | None = None,
) -> list[dict]:
    from app.rag.embeddings import embed_text

    if min_score is None:
        if use_openai_embeddings():
            min_score = settings.rag_min_score_openai
        else:
            min_score = settings.rag_min_score_mock

    query_vector = embed_text(query)
    scored: list[tuple[float, dict]] = []
    for entry in get_index():
        score = cosine_similarity(query_vector, entry["vector"])
        if score >= min_score:
            scored.append((score, entry["chunk"]))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [_chunk_hit(chunk, score, "embedding") for score, chunk in scored[:top_k]]


def resolve_rag_mode() -> str:
    mode = settings.rag_mode.strip().lower()
    if mode in {"keyword", "embedding"}:
        return mode
    if use_openai_embeddings():
        return "embedding"
    return "embedding" if settings.rag_use_mock_embeddings else "keyword"


def _rerank_hits(query: str, hits: list[dict]) -> list[dict]:
    """Blend vector score with keyword overlap for more stable FAQ ranking."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return hits

    for hit in hits:
        text_tokens = _tokenize(hit["title"] + " " + hit["text"])
        keyword_score = len(query_tokens & text_tokens) / len(query_tokens)
        vector_score = float(hit.get("score", 0))
        hit["score"] = round(vector_score * 0.55 + keyword_score * 0.45, 3)

    hits.sort(key=lambda item: item["score"], reverse=True)
    return hits


def search_knowledge(query: str, top_k: int = 3, min_score: float | None = None) -> list[dict]:
    """Hybrid retriever: embedding index with keyword fallback."""
    mode = resolve_rag_mode()
    if mode == "embedding":
        hits = search_embedding(query, top_k=top_k, min_score=min_score)
        if not hits:
            hits = search_keyword(query, top_k=top_k, min_score=min_score or 0.15)
        return _rerank_hits(query, hits)[:top_k]

    hits = search_keyword(query, top_k=top_k, min_score=min_score or 0.15)
    if hits:
        return hits
    hits = search_embedding(query, top_k=top_k, min_score=min_score)
    return _rerank_hits(query, hits)[:top_k]
