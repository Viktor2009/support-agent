"""Push intent eval / A/B results to Langfuse for dashboard comparison."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.eval_intent import evaluate_intent_dataset


def get_langfuse_client():
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    try:
        from langfuse import Langfuse
    except ImportError:
        return None
    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )


def push_variant_scores(client, *, variant: str, report: dict, run_id: str) -> int:
    """Create Langfuse traces + scores for each eval item. Returns count pushed."""
    from langfuse import Langfuse

    pushed = 0
    for index, item in enumerate(report.get("items", [])):
        trace_id = Langfuse.create_trace_id(seed=f"{run_id}:{variant}:{index}")
        client.create_event(
            trace_context={"trace_id": trace_id},
            name="intent-eval",
            input={
                "message": item["message"],
                "expected_intent": item["expected"],
            },
            output={"intent": item["got"]},
            metadata={
                "variant": variant,
                "prompt": report.get("prompt"),
                "run_id": run_id,
                "correct": item["correct"],
            },
        )
        client.create_score(
            trace_id=trace_id,
            name="intent_correct",
            value=1.0 if item["correct"] else 0.0,
            data_type="NUMERIC",
            comment=f"expected={item['expected']} got={item['got']}",
            metadata={"variant": variant, "run_id": run_id},
        )
        pushed += 1
    client.flush()
    return pushed


def run_ab_eval(
    *,
    use_real_llm: bool = False,
    push_langfuse: bool = True,
) -> dict[str, Any]:
    """Run A/B intent eval (prompt variant a vs b) and optionally push to Langfuse."""
    run_id = datetime.now(UTC).strftime("ab-eval-%Y%m%d-%H%M%S")
    variants: dict[str, dict] = {}
    for variant in ("a", "b"):
        variants[variant] = evaluate_intent_dataset(
            variant=variant,
            use_real_llm=use_real_llm,
        )

    if variants["a"].get("skipped") or variants["b"].get("skipped"):
        return {
            "skipped": True,
            "passed": True,
            "reason": variants["a"].get("reason") or variants["b"].get("reason"),
            "run_id": run_id,
            "variants": variants,
        }

    langfuse_pushed = 0
    langfuse_status = "disabled"
    client = get_langfuse_client() if push_langfuse else None
    if client is not None:
        for variant, report in variants.items():
            langfuse_pushed += push_variant_scores(
                client, variant=variant, report=report, run_id=run_id
            )
        langfuse_status = "pushed"
    elif push_langfuse:
        langfuse_status = "not_configured"

    winner = "a"
    if variants["b"]["accuracy_pct"] > variants["a"]["accuracy_pct"]:
        winner = "b"
    elif variants["b"]["accuracy_pct"] == variants["a"]["accuracy_pct"]:
        winner = "tie"

    passed = variants["a"]["passed"] and variants["b"]["passed"]
    return {
        "run_id": run_id,
        "passed": passed,
        "winner": winner,
        "langfuse": langfuse_status if push_langfuse else "disabled",
        "langfuse_scores_pushed": langfuse_pushed,
        "comparison": {
            "a_accuracy_pct": variants["a"]["accuracy_pct"],
            "b_accuracy_pct": variants["b"]["accuracy_pct"],
            "delta_pct": round(
                variants["b"]["accuracy_pct"] - variants["a"]["accuracy_pct"],
                1,
            ),
        },
        "variants": {
            variant: {
                "accuracy_pct": report["accuracy_pct"],
                "correct": report["correct"],
                "total": report["total"],
                "prompt": report["prompt"],
                "failures": report["failures"],
            }
            for variant, report in variants.items()
        },
    }
