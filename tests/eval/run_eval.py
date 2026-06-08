"""Offline evaluation against golden intent dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.eval_intent import evaluate_intent_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Golden dataset intent eval")
    parser.add_argument(
        "--real-llm",
        action="store_true",
        help="Use OpenAI (requires OPENAI_API_KEY); skips if missing",
    )
    parser.add_argument(
        "--variant",
        choices=["a", "b"],
        default="a",
        help="Prompt variant for A/B testing",
    )
    args = parser.parse_args()
    report = evaluate_intent_dataset(variant=args.variant, use_real_llm=args.real_llm)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report.get("skipped"):
        raise SystemExit(0)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
