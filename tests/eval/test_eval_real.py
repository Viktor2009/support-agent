from tests.eval.run_eval import run_eval


def test_real_llm_eval_skips_without_api_key(monkeypatch):
    monkeypatch.setattr("tests.eval.run_eval.settings.openai_api_key", "")
    report = run_eval(use_real_llm=True)
    assert report.get("skipped") is True
    assert report["passed"] is True
