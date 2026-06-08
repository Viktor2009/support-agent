import re

from app.rag.loader import load_chunks


def _tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]+", text.lower()) if len(w) > 2}


def search_knowledge(query: str, top_k: int = 3, min_score: float = 0.15) -> list[dict]:
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

    scored.sort(key=lambda x: x[0], reverse=True)
    results: list[dict] = []
    for score, chunk in scored[:top_k]:
        results.append(
            {
                "source_type": "knowledge",
                "source_id": chunk["id"],
                "title": chunk["title"],
                "text": chunk["text"],
                "score": round(score, 3),
            }
        )
    return results
