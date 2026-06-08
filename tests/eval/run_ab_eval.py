"""A/B intent eval with optional Langfuse dashboard export."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.langfuse_eval import run_ab_eval


def main() -> None:
    parser = argparse.ArgumentParser(description="A/B intent eval (variant a vs b)")
    parser.add_argument("--real-llm", action="store_true")
    parser.add_argument(
        "--no-langfuse",
        action="store_true",
        help="Do not push scores to Langfuse",
    )
    args = parser.parse_args()
    report = run_ab_eval(
        use_real_llm=args.real_llm,
        push_langfuse=not args.no_langfuse,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report.get("skipped"):
        raise SystemExit(0)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
