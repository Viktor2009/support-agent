from app.eval_intent import evaluate_intent_dataset


def test_real_llm_eval_skips_without_api_key(monkeypatch):
    monkeypatch.setattr("app.eval_intent.settings.openai_api_key", "")
    report = evaluate_intent_dataset(use_real_llm=True)
    assert report.get("skipped") is True
    assert report["passed"] is True
