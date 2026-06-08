"""Offline evaluation against golden intent dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from langchain_core.messages import HumanMessage

from app.config import settings
from app.database import configure_database
from app.graph import nodes

DATASET = Path(__file__).parent / "golden_dataset.jsonl"


def run_eval(*, use_real_llm: bool = False) -> dict:
    if use_real_llm:
        if not settings.openai_api_key:
            return {
                "skipped": True,
                "passed": True,
                "reason": "OPENAI_API_KEY not set",
                "mode": "real_llm",
            }
        settings.mock_llm = False
        mode = "real_llm"
    else:
        settings.mock_llm = True
        settings.openai_api_key = ""
        mode = "mock_llm"

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
            "messages": [HumanMessage(content=row["message"])],
            "dialog_summary": "",
        }
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
        "mode": mode,
        "total": total,
        "correct": correct,
        "accuracy_pct": accuracy,
        "failures": failures,
        "passed": accuracy >= 85.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Golden dataset intent eval")
    parser.add_argument(
        "--real-llm",
        action="store_true",
        help="Use OpenAI (requires OPENAI_API_KEY); skips if missing",
    )
    args = parser.parse_args()
    report = run_eval(use_real_llm=args.real_llm)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report.get("skipped"):
        raise SystemExit(0)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
