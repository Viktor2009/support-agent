"""Intent evaluation helpers (golden dataset, A/B prompt variants)."""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.messages import HumanMessage

from app.cache import reset_cache
from app.config import settings
from app.database import configure_database
from app.graph import nodes

GOLDEN_DATASET = (
    Path(__file__).resolve().parent.parent / "tests" / "eval" / "golden_dataset.jsonl"
)


def intent_prompt_name(variant: str) -> str:
    return "classify_intent_b" if variant == "b" else "classify_intent"


def evaluate_intent_dataset(
    *,
    variant: str = "a",
    use_real_llm: bool = False,
    dataset_path: Path | None = None,
) -> dict:
    """Run golden dataset intent classification for one prompt variant."""
    if use_real_llm:
        if not settings.openai_api_key:
            return {
                "skipped": True,
                "passed": True,
                "reason": "OPENAI_API_KEY not set",
                "variant": variant,
                "mode": "real_llm",
            }
        settings.mock_llm = False
        mode = "real_llm"
    else:
        settings.mock_llm = True
        settings.openai_api_key = ""
        mode = "mock_llm"

    previous_variant = settings.eval_prompt_variant
    settings.eval_prompt_variant = variant
    reset_cache()

    db_file = Path(__file__).resolve().parent.parent / f".eval-{variant}.db"
    configure_database(f"sqlite:///{db_file.as_posix()}")

    path = dataset_path or GOLDEN_DATASET
    total = 0
    correct = 0
    failures: list[dict] = []
    items: list[dict] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        total += 1
        state = {
            "session_id": f"eval-{variant}",
            "customer_id": row["customer_id"],
            "messages": [HumanMessage(content=row["message"])],
            "dialog_summary": "",
        }
        result = nodes.classify_intent(state)
        got = result["intent"]
        expected = row["expected_intent"]
        is_correct = got == expected
        if is_correct:
            correct += 1
        else:
            failures.append(
                {
                    "message": row["message"],
                    "expected": expected,
                    "got": got,
                }
            )
        items.append(
            {
                "message": row["message"],
                "expected": expected,
                "got": got,
                "correct": is_correct,
            }
        )

    settings.eval_prompt_variant = previous_variant
    accuracy = round(correct / total * 100, 1) if total else 0.0
    return {
        "variant": variant,
        "prompt": intent_prompt_name(variant),
        "mode": mode,
        "total": total,
        "correct": correct,
        "accuracy_pct": accuracy,
        "failures": failures,
        "items": items,
        "passed": accuracy >= 85.0,
    }
