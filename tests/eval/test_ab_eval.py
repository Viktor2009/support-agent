from app.langfuse_eval import run_ab_eval


def test_ab_eval_mock_passes():
    report = run_ab_eval(use_real_llm=False, push_langfuse=False)
    assert report["passed"] is True
    assert report["variants"]["a"]["accuracy_pct"] >= 85.0
    assert report["variants"]["b"]["accuracy_pct"] >= 85.0
    assert report["winner"] in {"a", "b", "tie"}
    assert report["langfuse"] == "disabled"
