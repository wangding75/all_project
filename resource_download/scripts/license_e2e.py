#!/usr/bin/env python3
"""Real HTTP RD -> License Service integration smoke test.

The script intentionally generates a temporary Python ED25519 Device identity
for the test run.  It never writes a Device private key into RD source/config
and never calls ``license_gateway.authorize`` directly.

Required environment variables:

``RD_BASE_URL``        RD HTTP base URL (default ``http://127.0.0.1:8000``)
``RD_LICENSE_KEY``     License Service activation key

Optional authentication variables:

``RD_ACCESS_TOKEN``     Existing RD JWT; otherwise the script registers/logs in
``RD_USERNAME`` / ``RD_PASSWORD`` (defaults are randomized for a test tenant)
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sys
from typing import Any

import requests
from license_service_client import activation_proof, generate_device_identity, request_proof


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _post_json(session: requests.Session, url: str, payload: dict[str, Any], headers: dict[str, str]):
    raw = _json_bytes(payload)
    merged = {"Content-Type": "application/json", **headers}
    return session.post(url, data=raw, headers=merged, timeout=10), raw


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    base_url = os.environ.get("RD_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    license_key = os.environ.get("RD_LICENSE_KEY", "").strip()
    if not license_key:
        _fail("RD_LICENSE_KEY is required for real activation E2E")

    session = requests.Session()
    token = os.environ.get("RD_ACCESS_TOKEN", "").strip()
    username = os.environ.get("RD_USERNAME", f"license_e2e_{secrets.token_hex(5)}")
    password = os.environ.get("RD_PASSWORD", f"E2E-{secrets.token_urlsafe(16)}")
    if not token:
        register = session.post(
            f"{base_url}/v1/auth/register",
            json={"username": username, "password": password},
            timeout=10,
        )
        if register.status_code not in (201, 400):
            _fail(f"register failed: HTTP {register.status_code}")
        login = session.post(
            f"{base_url}/v1/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if login.status_code != 200:
            _fail(f"login failed: HTTP {login.status_code}")
        token = str(login.json().get("access_token") or "")
    if not token:
        _fail("RD JWT was not returned")

    device_id, device_private, device_public = generate_device_identity()
    auth_headers = {"Authorization": f"Bearer {token}"}
    activate_payload = {
        "card_code": license_key,
        "device_id": device_id,
        "device_key_algorithm": "ED25519",
        "device_public_key": device_public,
        "proof": activation_proof(
            device_private,
            audience="rd",
            license_key=license_key,
            device_id=device_id,
            public_key_b64=device_public,
        ),
    }
    response, _raw = _post_json(
        session,
        f"{base_url}/v1/auth/redeem",
        activate_payload,
        auth_headers,
    )
    if response.status_code != 200 or not response.json().get("success"):
        _fail(f"activation failed: HTTP {response.status_code} detail={response.json().get('detail', '')}")
    print("activation PASS")

    job_payload = {
        "platform": "fanqie",
        "id": os.environ.get("RD_E2E_ITEM_ID", "license-e2e-item"),
        "range": "1-1",
        "options": {},
    }
    job_raw = _json_bytes(job_payload)
    job_target = "/v1/jobs"
    job_proof = request_proof(
        device_private,
        audience="rd",
        method="POST",
        request_target=job_target,
        body_sha256=hashlib.sha256(job_raw).hexdigest(),
    )
    device_headers = {
        "X-Device-Id": device_id,
        "X-Device-Key-Algorithm": "ED25519",
        "X-Device-Proof-Timestamp": str(job_proof["timestamp"]),
        "X-Device-Proof-Nonce": job_proof["nonce"],
        "X-Device-Proof-Signature": job_proof["signature"],
    }
    job_response = session.post(
        f"{base_url}{job_target}",
        data=job_raw,
        headers={"Content-Type": "application/json", **auth_headers, **device_headers},
        timeout=15,
    )
    if job_response.status_code != 200:
        _fail(f"ACTIVE job failed: HTTP {job_response.status_code} detail={job_response.text[:200]}")
    print("ACTIVE job request PASS")
    print("SERVER INTEGRATION PASS")
    print("CLIENT CUTOVER PENDING (this script is the temporary real-proof test client)")


if __name__ == "__main__":
    main()
