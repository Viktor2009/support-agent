import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.database import configure_database
from app.main import app
from app.service import reset_all


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    """Fresh SQLite DB and mock LLM for every test."""
    monkeypatch.setattr(settings, "mock_llm", True)
    monkeypatch.setattr(settings, "openai_api_key", "")
    db_file = (tmp_path / "support.db").as_posix()
    configure_database(f"sqlite:///{db_file}")
    reset_all()
    yield
    reset_all()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
