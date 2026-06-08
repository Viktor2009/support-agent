from app.langfuse_eval import get_langfuse_client, run_ab_eval


def test_langfuse_client_none_without_keys(monkeypatch):
    monkeypatch.setattr("app.langfuse_eval.settings.langfuse_public_key", "")
    monkeypatch.setattr("app.langfuse_eval.settings.langfuse_secret_key", "")
    assert get_langfuse_client() is None


def test_ab_eval_langfuse_not_configured(monkeypatch):
    monkeypatch.setattr("app.langfuse_eval.settings.langfuse_public_key", "")
    report = run_ab_eval(use_real_llm=False, push_langfuse=True)
    assert report["langfuse"] == "not_configured"
