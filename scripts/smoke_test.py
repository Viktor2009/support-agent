"""Staging smoke test: health, chat, metrics, widget, admin."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

import httpx


async def run_smoke(
    *,
    base_url: str,
    api_key: str | None,
    admin_key: str | None,
) -> dict:
    headers: dict[str, str] = {}
    if api_key:
        headers["X-API-Key"] = api_key
    admin_headers = {"X-Admin-Key": admin_key} if admin_key else {}

    checks: list[dict] = []
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:

        async def check(name: str, coro) -> None:
            try:
                result = await coro
                checks.append({"name": name, "ok": True, **result})
            except Exception as exc:
                checks.append({"name": name, "ok": False, "error": str(exc)})

        async def health():
            response = await client.get("/health")
            response.raise_for_status()
            data = response.json()
            assert data.get("status") == "ok", data
            return {"status": data.get("status"), "database": data.get("database")}

        async def chat():
            response = await client.post(
                "/chat",
                headers=headers,
                json={
                    "session_id": "smoke-1",
                    "message": "Где мой заказ #1?",
                },
            )
            response.raise_for_status()
            data = response.json()
            assert "answer" in data or "status" in data, data
            return {"keys": list(data.keys())[:5]}

        async def metrics():
            response = await client.get("/metrics")
            response.raise_for_status()
            body = response.text
            assert "support_chat_requests_total" in body, "missing prometheus metrics"
            return {"bytes": len(body)}

        async def widget():
            response = await client.get("/widget/")
            response.raise_for_status()
            return {"status_code": response.status_code}

        async def admin_stats():
            response = await client.get("/admin/api/stats", headers=admin_headers)
            response.raise_for_status()
            return response.json()

        await check("health", health())
        await check("chat", chat())
        await check("metrics", metrics())
        await check("widget", widget())
        if admin_key:
            await check("admin_stats", admin_stats())

    passed = sum(1 for item in checks if item["ok"])
    return {
        "base_url": base_url,
        "passed": passed,
        "total": len(checks),
        "ok": passed == len(checks),
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test Support Agent staging")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--admin-key", default=None)
    args = parser.parse_args()

    report = asyncio.run(
        run_smoke(
            base_url=args.url.rstrip("/"),
            api_key=args.api_key,
            admin_key=args.admin_key,
        )
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
