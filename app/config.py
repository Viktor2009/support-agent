from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    mock_llm: bool = False
    database_url: str = "sqlite:///./support.db"


settings = Settings()


def is_postgres() -> bool:
    return settings.database_url.startswith("postgresql")
