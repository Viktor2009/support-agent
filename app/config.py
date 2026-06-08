from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    mock_llm: bool = False
    database_url: str = "sqlite:///./support.db"

    # Auth: "customer_id:api_key,customer_id2:api_key2" — пусто = auth выключен
    api_keys: str = ""

    # CORS: "*" или comma-separated origins
    cors_origins: str = "*"

    # Langfuse (optional)
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    app_version: str = "1.1.0"

    # RAG: auto | keyword | embedding
    rag_mode: str = "auto"
    rag_use_mock_embeddings: bool = True
    embedding_model: str = "text-embedding-3-small"
    rag_min_score_mock: float = 0.05
    rag_min_score_openai: float = 0.35

    # Cache / Redis (optional — empty = in-memory only)
    redis_url: str = ""
    cache_ttl_seconds: int = 300
    intent_cache_ttl_seconds: int = 120

    # Rate limiting (requests per minute per IP, 0 = disabled)
    rate_limit_per_minute: int = 60

    # Admin panel API key
    admin_api_key: str = ""

    # Zendesk (optional)
    zendesk_subdomain: str = ""
    zendesk_email: str = ""
    zendesk_api_token: str = ""
    zendesk_mock: bool = True


settings = Settings()


def is_postgres() -> bool:
    return settings.database_url.startswith("postgresql")


def to_async_database_url(url: str) -> str:
    """Convert sync SQLAlchemy URL to async driver URL."""
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def parse_api_keys(raw: str) -> dict[str, tuple[str, str]]:
    """Map api_key -> (tenant_id, customer_id)."""
    mapping: dict[str, tuple[str, str]] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        segments = [segment.strip() for segment in part.split(":") if segment.strip()]
        if len(segments) == 2:
            tenant_id, customer_id, api_key = "default", segments[0], segments[1]
        elif len(segments) >= 3:
            tenant_id, customer_id, api_key = segments[0], segments[1], segments[2]
        else:
            continue
        if tenant_id and customer_id and api_key:
            mapping[api_key] = (tenant_id, customer_id)
    return mapping


def parse_cors_origins(raw: str) -> list[str]:
    raw = raw.strip()
    if raw == "*" or not raw:
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def auth_enabled() -> bool:
    return bool(parse_api_keys(settings.api_keys))
