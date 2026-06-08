from fastapi import APIRouter, Depends, HTTPException

from app.auth import AuthContext, get_auth_context, resolve_customer_id, resolve_tenant_id
from app.gdpr import delete_session_data, export_session_data
from app.privacy import mask_payload

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


@router.get("/sessions/{session_id}/export")
def export_session(
    session_id: str,
    auth: AuthContext | None = Depends(get_auth_context),
    customer_id: str | None = None,
    mask_pii: bool = True,
):
    tenant_id = resolve_tenant_id(auth)
    resolved_customer = resolve_customer_id(auth, customer_id)
    try:
        payload = export_session_data(session_id, tenant_id=tenant_id, customer_id=resolved_customer)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if mask_pii:
        payload = mask_payload(payload)
    return payload


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    auth: AuthContext | None = Depends(get_auth_context),
    customer_id: str | None = None,
):
    tenant_id = resolve_tenant_id(auth)
    resolved_customer = resolve_customer_id(auth, customer_id)
    try:
        delete_session_data(session_id, tenant_id=tenant_id, customer_id=resolved_customer)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "deleted", "session_id": session_id}
