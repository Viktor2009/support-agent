import pytest
from fastapi.testclient import TestClient

from app.cache import reset_cache
from app.config import settings
from app.database import configure_database
from app.main import app
from app.rag.loader import reset_chunks
from app.rate_limit import reset_rate_limit
from app.service import reset_all


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    """Fresh SQLite DB and mock LLM for every test."""
    monkeypatch.setattr(settings, "mock_llm", True)
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "api_keys", "")
    monkeypatch.setattr(settings, "admin_api_key", "")
    monkeypatch.setattr(settings, "rate_limit_per_minute", 0)
    db_file = (tmp_path / "support.db").as_posix()
    configure_database(f"sqlite:///{db_file}")
    reset_chunks()
    reset_cache()
    reset_rate_limit()
    reset_all()
    yield
    reset_all()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
