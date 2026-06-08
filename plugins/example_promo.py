"""Example plugin: promo code lookup (demo only)."""

from __future__ import annotations

from app.tenant import DEFAULT_TENANT

_PROMOS = {
    "SAVE10": {"discount_pct": 10, "description": "10% off next order"},
    "FREESHIP": {"discount_pct": 0, "description": "Free shipping"},
}


async def lookup_promo(code: str, *, tenant_id: str = DEFAULT_TENANT) -> dict:
    """Look up a promotional code (demo data)."""
    normalized = code.strip().upper()
    promo = _PROMOS.get(normalized)
    if promo is None:
        return {"found": False, "code": normalized, "tenant_id": tenant_id}
    return {"found": True, "code": normalized, "tenant_id": tenant_id, **promo}


def register(register_tool) -> None:
    register_tool("lookup_promo", lookup_promo)
