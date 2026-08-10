"""FastAPI transport guard for RD Device Proof V3 requests."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from fastapi import Depends, HTTPException, Request, status

from app.auth import Identity, require_identity
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


async def require_active_device_license(
    request: Request,
    identity: Identity = Depends(require_identity),
    gateway: LicenseGateway = Depends(get_license_gateway),
) -> Identity:
    """Require identity plus an ACTIVE License decision for the real request."""
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
