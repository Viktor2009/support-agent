import pytest

from app.prompts import get_prompt


def test_get_classify_prompt():
    text = get_prompt(
        "classify_intent",
        dialog_summary="summary",
        message="Где заказ?",
    )
    assert "order_status" in text
    assert "summary" in text
    assert "Где заказ?" in text


def test_missing_prompt_raises():
    with pytest.raises(KeyError):
        get_prompt("nonexistent_prompt_xyz")
