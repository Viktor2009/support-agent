"""Simple concurrent load test for /chat (default: 50 sessions)."""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time

import httpx


async def one_chat(
    client: httpx.AsyncClient,
    *,
    session_id: str,
    message: str,
    customer_id: str,
) -> tuple[int, float]:
    started = time.perf_counter()
    response = await client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": message,
            "customer_id": customer_id,
        },
    )
    elapsed = time.perf_counter() - started
    return response.status_code, elapsed


async def run_load_test(
    *,
    base_url: str,
    concurrency: int,
    customer_id: str,
) -> dict:
    async with httpx.AsyncClient(base_url=base_url, timeout=60.0) as client:
        health = await client.get("/health")
        health.raise_for_status()

        tasks = [
            one_chat(
                client,
                session_id=f"load-{index}",
                message="Где мой заказ #1?",
                customer_id=customer_id,
            )
            for index in range(concurrency)
        ]
        started = time.perf_counter()
        results = await asyncio.gather(*tasks)
        total = time.perf_counter() - started

    statuses = [status for status, _ in results]
    latencies = [elapsed for _, elapsed in results]
    ok = sum(1 for status in statuses if status == 200)
    return {
        "concurrency": concurrency,
        "ok": ok,
        "failed": concurrency - ok,
        "total_seconds": round(total, 2),
        "p50_ms": round(statistics.median(latencies) * 1000, 1),
        "p95_ms": round(statistics.quantiles(latencies, n=20)[-1] * 1000, 1)
        if len(latencies) >= 2
        else round(latencies[0] * 1000, 1),
        "status_codes": sorted(set(statuses)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Load test Support Agent /chat")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--concurrency", type=int, default=50)
    parser.add_argument("--customer-id", default="cust_456")
    args = parser.parse_args()

    report = asyncio.run(
        run_load_test(
            base_url=args.url,
            concurrency=args.concurrency,
            customer_id=args.customer_id,
        )
    )
    print(report)
    if report["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
