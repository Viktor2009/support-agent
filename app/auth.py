from dataclasses import dataclass

from fastapi import Header, HTTPException

from app.config import parse_api_keys, settings
from app.tenant import DEFAULT_TENANT


@dataclass(frozen=True)
class AuthContext:
    tenant_id: str
    customer_id: str


def resolve_customer_id(
    auth: AuthContext | None,
    body_customer_id: str | None,
) -> str:
    if auth is not None:
        if body_customer_id and body_customer_id != auth.customer_id:
            raise HTTPException(
                status_code=403,
                detail="customer_id in body does not match API key",
            )
        return auth.customer_id
    if not body_customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required")
    return body_customer_id


def resolve_tenant_id(auth: AuthContext | None, body_tenant_id: str | None = None) -> str:
    if auth is not None:
        if body_tenant_id and body_tenant_id != auth.tenant_id:
            raise HTTPException(status_code=403, detail="tenant_id does not match API key")
        return auth.tenant_id
    return body_tenant_id or DEFAULT_TENANT


def get_auth_context(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> AuthContext | None:
    keys = parse_api_keys(settings.api_keys)
    if not keys:
        return None
    if not x_api_key or x_api_key not in keys:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    tenant_id, customer_id = keys[x_api_key]
    return AuthContext(tenant_id=tenant_id, customer_id=customer_id)
