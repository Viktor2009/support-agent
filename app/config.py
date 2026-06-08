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

    app_version: str = "0.2.0"


settings = Settings()


def is_postgres() -> bool:
    return settings.database_url.startswith("postgresql")


def parse_api_keys(raw: str) -> dict[str, str]:
    """Map api_key -> customer_id."""
    mapping: dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        customer_id, api_key = part.split(":", 1)
        customer_id = customer_id.strip()
        api_key = api_key.strip()
        if customer_id and api_key:
            mapping[api_key] = customer_id
    return mapping


def parse_cors_origins(raw: str) -> list[str]:
    raw = raw.strip()
    if raw == "*" or not raw:
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def auth_enabled() -> bool:
    return bool(parse_api_keys(settings.api_keys))
