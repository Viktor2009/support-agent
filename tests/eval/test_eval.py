from tests.eval.run_eval import run_eval


def test_golden_dataset_eval_passes():
    report = run_eval()
    assert report["total"] >= 16
    assert report["accuracy_pct"] >= 85.0
