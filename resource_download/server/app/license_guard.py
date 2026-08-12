"""FastAPI transport guard for RD Device Proof V3 requests."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from fastapi import Depends, Header, HTTPException, Request, status

from app.auth import Identity, decode_jwt
from app.config import get_settings
from app.license_gateway import LicenseGateway, get_license_gateway

DEVICE_PROOF_HEADER_NAMES = (
    "X-Device-Id",
    "X-Device-Key-Algorithm",
    "X-Device-Proof-Timestamp",
    "X-Device-Proof-Nonce",
    "X-Device-Proof-Signature",
)

_INACTIVE_REASONS = {
    "DEVICE_PROOF_EXPIRED",
    "INVALID_DEVICE_PROOF",
    "DEVICE_PROOF_REPLAYED",
    "DEVICE_NOT_ACTIVATED",
    "DEVICE_REVOKED",
    "LICENSE_EXPIRED",
    "LICENSE_REVOKED",
    "DEVICE_LIMIT_REACHED",
    "PLAN_ENTITLEMENT_INVALID",
}
_UNKNOWN_REASONS = {
    "LICENSE_SERVICE_UNAVAILABLE",
    "LICENSE_SERVICE_TIMEOUT",
    "LICENSE_SERVICE_REJECTED",
}


def _request_target(request: Request) -> str:
    path = str(request.scope.get("path") or request.url.path)
    query = request.scope.get("query_string") or b""
    if query:
        # query_string is the raw wire query; latin-1 preserves every byte 1:1.
        return f"{path}?{bytes(query).decode('latin-1')}"
    return path


def _proof_from_headers(request: Request) -> tuple[str, str, dict[str, Any]] | None:
    headers = request.headers
    values = {name: headers.get(name) for name in DEVICE_PROOF_HEADER_NAMES}
    if any(not value for value in values.values()):
        return None
    try:
        timestamp = int(values["X-Device-Proof-Timestamp"] or "")
    except (TypeError, ValueError):
        timestamp = values["X-Device-Proof-Timestamp"]
    return (
        str(values["X-Device-Id"]),
        str(values["X-Device-Key-Algorithm"]),
        {
            "timestamp": timestamp,
            "nonce": str(values["X-Device-Proof-Nonce"]),
            "signature": str(values["X-Device-Proof-Signature"]),
        },
    )


def _business_identity(
    x_api_key: str | None,
    authorization: str | None,
) -> Identity:
    """Build an optional legacy marker; License Context is the real identity.

    Desktop business requests do not require register/login/JWT.  If an old
    client still sends a valid JWT, its subject is retained only as a nullable
    compatibility/display marker and never authorizes the request.
    """
    settings = get_settings()
    if x_api_key and x_api_key == settings.api_key:
        return Identity(kind="api_key", is_ops=True)
    if authorization:
        parts = authorization.strip().split(None, 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            try:
                payload = decode_jwt(parts[1].strip())
                user_id = int(payload["sub"])
                return Identity(
                    kind="user",
                    user_id=user_id,
                    username=str(payload.get("username") or "") or None,
                )
            except Exception:  # invalid legacy marker does not bypass License
                pass
    return Identity(kind="license")


async def require_active_device_license(
    request: Request,
    gateway: LicenseGateway = Depends(get_license_gateway),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> Identity:
    """Require identity plus an ACTIVE License decision for the real request."""
    identity = _business_identity(x_api_key, authorization)
    parsed = _proof_from_headers(request)
    if parsed is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DEVICE_PROOF_REQUIRED",
        )
    device_id, key_algorithm, device_proof = parsed
    if not isinstance(device_proof.get("timestamp"), int):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DEVICE_PROOF_INVALID",
        )
    raw_body = await request.body()
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = request_id
    result = await asyncio.to_thread(
        gateway.authorize_request,
        device_id=device_id,
        request_method=request.method,
        request_target=_request_target(request),
        raw_body=raw_body,
        device_proof=device_proof,
        device_key_algorithm=key_algorithm,
        request_id=request_id,
    )
    decision = str(result.get("decision") or "UNKNOWN")
    reason = str(result.get("reason") or "")
    request.state.license_result = result
    if decision == "ACTIVE":
        context = {
            "license_id": result.get("license_id"),
            "device_id": result.get("device_id") or device_id,
            "plan_code": None,
            "plan_version": None,
            "entitlement_schema_version": result.get("entitlement_schema_version"),
            "entitlements": result.get("entitlements"),
        }
        plan = result.get("plan")
        if isinstance(plan, dict):
            context["plan_code"] = plan.get("code")
            context["plan_version"] = plan.get("version")
        valid_context = (
            isinstance(context["license_id"], str)
            and bool(context["license_id"].strip())
            and context["device_id"] == device_id
            and isinstance(context["plan_code"], str)
            and bool(context["plan_code"].strip())
            and isinstance(context["plan_version"], int)
            and not isinstance(context["plan_version"], bool)
            and context["plan_version"] >= 1
            and isinstance(context["entitlement_schema_version"], int)
            and not isinstance(context["entitlement_schema_version"], bool)
            and context["entitlement_schema_version"] >= 1
            and isinstance(context["entitlements"], dict)
        )
        # Existing offline unit doubles predate rc4.  Keep that test seam
        # isolated; a configured remote gateway with a partial response fails
        # closed instead of manufacturing a plan or quota.
        if not valid_context and hasattr(gateway, "client"):
            request.state.license_result = {
                "activated": False,
                "decision": "INACTIVE",
                "reason": "PLAN_ENTITLEMENT_INVALID",
                "source": "remote",
            }
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="PLAN_ENTITLEMENT_INVALID")
        if not valid_context:
            context = {
                "license_id": (
                    f"legacy:{identity.kind}:{identity.user_id}"
                    if identity.user_id is not None
                    else f"legacy:{identity.kind}"
                ),
                "device_id": device_id,
                "plan_code": "legacy",
                "plan_version": 1,
                "entitlement_schema_version": 1,
                "entitlements": {
                    "quota.daily_jobs": int(get_settings().vip_jobs_per_day),
                    "job.max_concurrency": 5,
                },
                "license_context_source": "legacy_compat",
            }
        else:
            context["license_context_source"] = "remote"
        identity = identity.model_copy(update=context)
        request.state.license_context = context
        # Only a Device-Proof-validated identity may be persisted as an
        # automation binding.  The body is never used for this value.
        request.state.verified_device_id = device_id
        request.state.verified_device_key_algorithm = key_algorithm
        return identity
    if decision == "INACTIVE":
        if reason == "INVALID_DEVICE_PROOF":
            reason = "DEVICE_PROOF_INVALID"
        elif reason not in _INACTIVE_REASONS:
            reason = "LICENSE_REQUIRED"
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=reason)

    if reason not in _UNKNOWN_REASONS:
        reason = "LICENSE_SERVICE_UNAVAILABLE"
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=reason)
