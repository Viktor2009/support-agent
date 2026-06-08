from app.eval_intent import evaluate_intent_dataset


def test_golden_dataset_eval_passes():
    report = evaluate_intent_dataset()
    assert report["total"] >= 16
    assert report["accuracy_pct"] >= 85.0
