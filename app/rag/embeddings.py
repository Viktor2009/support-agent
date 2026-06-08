from langchain_openai import OpenAIEmbeddings

from app.config import settings
from app.rag.vectors import mock_embedding


def use_openai_embeddings() -> bool:
    return bool(settings.openai_api_key) and not settings.mock_llm


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if use_openai_embeddings():
        client = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
        )
        return client.embed_documents(texts)
    return [mock_embedding(text) for text in texts]
