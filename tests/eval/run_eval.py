"""Offline evaluation against golden intent dataset."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.config import settings
from app.database import configure_database
from app.graph import nodes

DATASET = Path(__file__).parent / "golden_dataset.jsonl"


def run_eval() -> dict:
    settings.mock_llm = True
    settings.openai_api_key = ""
    configure_database(f"sqlite:///{(ROOT / '.eval.db').as_posix()}")

    total = 0
    correct = 0
    failures: list[dict] = []

    for line in DATASET.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        total += 1
        state = {
            "session_id": "eval",
            "customer_id": row["customer_id"],
            "messages": [],
            "dialog_summary": "",
        }
        from langchain_core.messages import HumanMessage

        state["messages"] = [HumanMessage(content=row["message"])]
        result = nodes.classify_intent(state)
        if result["intent"] == row["expected_intent"]:
            correct += 1
        else:
            failures.append(
                {
                    "message": row["message"],
                    "expected": row["expected_intent"],
                    "got": result["intent"],
                }
            )

    accuracy = round(correct / total * 100, 1) if total else 0.0
    return {
        "total": total,
        "correct": correct,
        "accuracy_pct": accuracy,
        "failures": failures,
        "passed": accuracy >= 85.0,
    }


if __name__ == "__main__":
    report = run_eval()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 1)
