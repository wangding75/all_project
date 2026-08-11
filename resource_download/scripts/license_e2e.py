#!/usr/bin/env python3
"""Real HTTP RD -> License Service integration E2E.

All business assertions in this runner use the RD HTTP API.  The optional
PostgreSQL helper is only for local fixture preparation (rebinding the
already-prepared expired/revoked licenses); it is never used as an
authorization substitute.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from license_service_client import activation_proof, generate_device_identity, request_proof


UTC = timezone.utc


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _detail(response: requests.Response) -> str:
    try:
        value = response.json().get("detail", "")
    except (ValueError, AttributeError):
        return ""
    return str(value)


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _pass(label: str) -> None:
    print(f"{label} PASS")


def _expect_status(
    response: requests.Response,
    expected: int,
    label: str,
    details: set[str] | None = None,
) -> None:
    if response.status_code != expected:
        _fail(f"{label} expected HTTP {expected}, got {response.status_code}")
    if details is not None and _detail(response) not in details:
        _fail(f"{label} returned unexpected denial reason")
    _pass(label)


def _proof_headers(
    device_private: str,
    device_id: str,
    target: str,
    raw_body: bytes,
    *,
    method: str = "POST",
) -> dict[str, str]:
    proof = request_proof(
        device_private,
        audience="rd",
        method=method,
        request_target=target,
        body_sha256=hashlib.sha256(raw_body).hexdigest(),
    )
    return {
        "X-Device-Id": device_id,
        "X-Device-Key-Algorithm": "ED25519",
        "X-Device-Proof-Timestamp": str(proof["timestamp"]),
        "X-Device-Proof-Nonce": proof["nonce"],
        "X-Device-Proof-Signature": proof["signature"],
    }


def _job_payload(label: str) -> dict[str, Any]:
    return {
        "platform": "fanqie",
        "id": f"license-e2e-{label}-{secrets.token_hex(4)}",
        "range": "1-1",
        "options": {},
    }


def _job_request(
    session: requests.Session,
    base_url: str,
    auth_headers: dict[str, str],
    device_id: str,
    device_private: str,
    payload: dict[str, Any],
    *,
    actual_target: str = "/v1/jobs",
    signed_target: str | None = None,
    proof_private: str | None = None,
    proof_device_id: str | None = None,
    raw_body: bytes | None = None,
) -> tuple[requests.Response, bytes, dict[str, str]]:
    raw = _json_bytes(payload) if raw_body is None else raw_body
    proof_headers = _proof_headers(
        proof_private or device_private,
        proof_device_id or device_id,
        signed_target or actual_target,
        raw if raw_body is None else _json_bytes(payload),
    )
    headers = {"Content-Type": "application/json", **auth_headers, **proof_headers}
    response = session.post(
        f"{base_url}{actual_target}",
        data=raw,
        headers=headers,
        timeout=15,
    )
    return response, raw, headers


def _compose_command(action: str) -> None:
    service_root = os.environ.get("LICENSE_SERVICE_ROOT", "").strip()
    if not service_root:
        _fail("LICENSE_SERVICE_ROOT is required for service lifecycle E2E")
    compose_env = os.environ.copy()
    compose_env["LICENSE_HOST_PORT"] = os.environ.get("LICENSE_HOST_PORT", "")
    result = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            ".env.e2e.local",
            "-f",
            "docker-compose.yml",
            "-f",
            "docker-compose.e2e.yml",
            action,
            "license-service",
        ],
        cwd=service_root,
        env=compose_env,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    if result.returncode != 0:
        _fail(f"License Service {action} command failed")


def _wait_license_ready(base_url: str, timeout: float = 90.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            response = requests.get(f"{base_url}/health/ready", timeout=3)
            if response.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(2)
    _fail("License Service did not become ready")


def _tenant_sql(sql: str) -> str:
    service_root = os.environ.get("LICENSE_SERVICE_ROOT", "").strip()
    tenant_db = os.environ.get("LICENSE_E2E_TENANT_DB", "").strip()
    postgres_user = os.environ.get("POSTGRES_USER", "").strip()
    postgres_password = os.environ.get("POSTGRES_PASSWORD", "")
    if not service_root or not tenant_db or not postgres_user or not postgres_password:
        _fail("local License fixture database environment is incomplete")
    compose_env = os.environ.copy()
    compose_env["LICENSE_HOST_PORT"] = os.environ.get("LICENSE_HOST_PORT", "")
    command = [
        "docker",
        "compose",
        "--env-file",
        ".env.e2e.local",
        "-f",
        "docker-compose.yml",
        "-f",
        "docker-compose.e2e.yml",
        "exec",
        "-T",
        "-e",
        f"PGPASSWORD={postgres_password}",
        "postgres",
        "psql",
        "-U",
        postgres_user,
        "-d",
        tenant_db,
        "-At",
        "-c",
        sql,
    ]
    result = subprocess.run(
        command,
        cwd=service_root,
        env=compose_env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        _fail("local License fixture SQL failed")
    return result.stdout.strip()


def _rebind_prepared_license(license_id: str, device_public_key: str) -> None:
    """Bind the current temporary proof key to a prepared scenario license.

    This is fixture setup only.  The subsequent check is always sent through
    RD HTTP and License Service HTTP.
    """
    safe_license_id = license_id.strip()
    if len(safe_license_id) != 36 or any(ch not in "0123456789abcdef-" for ch in safe_license_id.lower()):
        _fail("prepared license id is invalid")
    if "'" in device_public_key:
        _fail("device public key contains an unsafe SQL character")
    device_identity_id = _tenant_sql(
        "select id from device_identities "
        f"where public_key='{device_public_key}' limit 1;"
    )
    target_binding_id = _tenant_sql(
        "select id from license_devices "
        f"where license_id='{safe_license_id}' limit 1;"
    )
    if not device_identity_id or not target_binding_id:
        _fail("prepared License scenario binding is missing")
    _tenant_sql(
        "begin;"
        f"update license_devices set status='REVOKED', revoked_at=now() "
        f"where device_identity_id='{device_identity_id}' and status='ACTIVE';"
        f"update license_devices set device_identity_id='{device_identity_id}', "
        "status='ACTIVE', activated_at=now(), last_checked_at=now(), revoked_at=null "
        f"where id='{target_binding_id}';"
        f"update licenses set active_device_count=(select count(*) from license_devices "
        f"where license_id='{safe_license_id}' and status='ACTIVE') where id='{safe_license_id}';"
        f"update licenses set active_device_count=(select count(*) from license_devices "
        "where license_devices.license_id=licenses.id and license_devices.status='ACTIVE' "
        f") where id in (select distinct license_id from license_devices where device_identity_id='{device_identity_id}');"
        "commit;"
    )


def _set_device_identity_status(device_public_key: str, status: str) -> None:
    if status not in {"ACTIVE", "REVOKED"}:
        _fail("invalid device identity fixture status")
    if "'" in device_public_key:
        _fail("device public key contains an unsafe SQL character")
    device_identity_id = _tenant_sql(
        "select id from device_identities "
        f"where public_key='{device_public_key}' limit 1;"
    )
    if not device_identity_id:
        _fail("temporary device identity is missing")
    _tenant_sql(
        f"update device_identities set status='{status}' "
        f"where id='{device_identity_id}';"
    )


def _prepare_local_legacy_fields(user_id: int) -> str:
    data_dir = os.environ.get("DATA_DIR", "").strip()
    if not data_dir:
        _fail("DATA_DIR is required for local legacy bypass fixture")
    database = Path(data_dir) / "app.db"
    if not database.exists():
        _fail("RD SQLite database is missing")
    card_code = f"LEGACY-T11-{secrets.token_urlsafe(12)}"
    expiry = (datetime.now(UTC) + timedelta(days=1)).replace(tzinfo=None).isoformat()
    with sqlite3.connect(database) as connection:
        connection.execute("update users set vip_expires_at=? where id=?", (expiry, user_id))
        connection.execute(
            "insert into card_keys(code,duration_days,batch_id,is_used,used_by_user_id,used_at,created_at) "
            "values(?,?,?,?,?,?,?)",
            (
                card_code,
                30,
                "T11",
                0,
                None,
                None,
                datetime.now(UTC).replace(tzinfo=None).isoformat(),
            ),
        )
        connection.commit()
    return card_code


def _assert_legacy_card_unused(card_code: str, database: Path) -> None:
    with sqlite3.connect(database) as connection:
        row = connection.execute("select is_used from card_keys where code=?", (card_code,)).fetchone()
    if row != (0,):
        _fail("legacy CardKey was consumed by the new activation path")


def _automation_request(
    session: requests.Session,
    base_url: str,
    auth_headers: dict[str, str],
    target: str,
    device_id: str,
    device_private: str,
    payload: dict[str, Any] | None = None,
    *,
    method: str = "POST",
) -> requests.Response:
    raw = _json_bytes(payload) if payload is not None else b""
    proof_headers = _proof_headers(
        device_private,
        device_id,
        target,
        raw,
        method=method,
    )
    headers = {"Content-Type": "application/json", **auth_headers, **proof_headers}
    request = getattr(session, method.lower())
    return request(f"{base_url}{target}", data=raw, headers=headers, timeout=30)


def _automation_file(user_id: int) -> Path:
    data_dir = os.environ.get("DATA_DIR", "").strip()
    if not data_dir:
        _fail("DATA_DIR is required for background automation E2E")
    return Path(data_dir) / "automation" / "hongguo_monitors.json"


def _mutate_automation_fixture(user_id: int, **updates: Any) -> None:
    """Local fixture preparation; the following scan remains RD HTTP + real service."""
    path = _automation_file(user_id)
    if not path.is_file():
        _fail("background automation fixture was not persisted")
    payload = json.loads(path.read_text(encoding="utf-8"))
    policy = payload.get(f"user:{user_id}")
    if not isinstance(policy, dict):
        _fail("background automation policy is missing")
    policy.update(updates)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _wait_background_status(
    session: requests.Session,
    base_url: str,
    auth_headers: dict[str, str],
    *,
    expected_error: str | None = None,
    timeout: float = 45,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        response = session.get(
            f"{base_url}/v1/automation/hongguo-new",
            headers=auth_headers,
            timeout=15,
        )
        if response.status_code == 200:
            last = response.json()
            if expected_error is None:
                if last.get("last_scan_at"):
                    return last
            elif expected_error in {
                str(last.get("last_error") or ""),
                *[str(log.get("message") or "") for log in last.get("logs") or []],
            }:
                return last
        time.sleep(2)
    _fail(f"background status did not reach expected state: {expected_error or 'scan'}")
    return last


def _restart_rd_for_fixture() -> None:
    restart_script = os.environ.get("RD_RESTART_SCRIPT", "").strip()
    if not restart_script:
        _fail("RD_RESTART_SCRIPT is required for legacy automation fixture E2E")
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", restart_script],
        timeout=90,
        check=False,
    )
    if result.returncode != 0:
        _fail("RD fixture restart failed")
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            if requests.get(f"{os.environ['RD_BASE_URL'].rstrip('/')}/health", timeout=5).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(2)
    _fail("RD did not recover after fixture restart")


def main() -> None:
    base_url = os.environ.get("RD_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    license_key = os.environ.get("RD_LICENSE_KEY", "").strip()
    license_base_url = os.environ.get("LICENSE_SERVICE_BASE_URL", "").strip().rstrip("/")
    if not license_key or not license_base_url:
        _fail("RD_LICENSE_KEY and LICENSE_SERVICE_BASE_URL are required")

    session = requests.Session()
    username = os.environ.get("RD_USERNAME", f"license_e2e_{secrets.token_hex(5)}")
    password = os.environ.get("RD_PASSWORD", f"E2E-{secrets.token_urlsafe(16)}")
    token = os.environ.get("RD_ACCESS_TOKEN", "").strip()
    if not token:
        register = session.post(
            f"{base_url}/v1/auth/register",
            json={"username": username, "password": password},
            timeout=10,
        )
        if register.status_code not in (201, 400):
            _fail("register failed")
        login = session.post(
            f"{base_url}/v1/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if login.status_code != 200:
            _fail("login failed")
        token = str(login.json().get("access_token") or "")
    if not token:
        _fail("RD JWT was not returned")
    auth_headers = {"Authorization": f"Bearer {token}"}

    me = session.get(f"{base_url}/v1/auth/me", headers=auth_headers, timeout=10)
    _expect_status(me, 200, "RD user HTTP")
    user_id = int(me.json()["id"])
    database = Path(os.environ["DATA_DIR"]) / "app.db"
    legacy_card = _prepare_local_legacy_fields(user_id)

    device_id, device_private, device_public = generate_device_identity()
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
    response = session.post(
        f"{base_url}/v1/auth/redeem",
        data=_json_bytes(activate_payload),
        headers={"Content-Type": "application/json", **auth_headers},
        timeout=15,
    )
    if response.status_code != 200 or not response.json().get("success"):
        _fail("activation failed")
    _pass("ACTIVATION")

    active_payload = _job_payload("active")
    active_response, _, _ = _job_request(
        session, base_url, auth_headers, device_id, device_private, active_payload
    )
    _expect_status(active_response, 200, "ACTIVE")

    not_activated_id, not_activated_private, not_activated_public = generate_device_identity()
    not_activated_response, _, _ = _job_request(
        session,
        base_url,
        auth_headers,
        not_activated_id,
        not_activated_private,
        _job_payload("not-activated"),
    )
    _expect_status(not_activated_response, 403, "NOT_ACTIVATED", {"DEVICE_NOT_ACTIVATED"})

    invalid_payload = _job_payload("invalid-proof")
    invalid_raw = _json_bytes(invalid_payload)
    invalid_headers = _proof_headers(device_private, device_id, "/v1/jobs", invalid_raw)
    signature = invalid_headers["X-Device-Proof-Signature"]
    invalid_headers["X-Device-Proof-Signature"] = (
        ("A" if signature[0] != "A" else "B") + signature[1:]
    )
    invalid_response = session.post(
        f"{base_url}/v1/jobs",
        data=invalid_raw,
        headers={"Content-Type": "application/json", **auth_headers, **invalid_headers},
        timeout=15,
    )
    _expect_status(invalid_response, 403, "INVALID_PROOF")

    wrong_id, wrong_private, _ = generate_device_identity()
    wrong_response, _, _ = _job_request(
        session,
        base_url,
        auth_headers,
        device_id,
        device_private,
        _job_payload("wrong-device-key"),
        proof_private=wrong_private,
        proof_device_id=wrong_id,
    )
    _expect_status(wrong_response, 403, "INVALID_PROOF_WRONG_DEVICE_KEY")

    replay_response, replay_raw, replay_headers = _job_request(
        session,
        base_url,
        auth_headers,
        device_id,
        device_private,
        _job_payload("replay"),
    )
    _expect_status(replay_response, 200, "REPLAY_FIRST")
    replay_again = session.post(
        f"{base_url}/v1/jobs",
        data=replay_raw,
        headers=replay_headers,
        timeout=15,
    )
    _expect_status(replay_again, 403, "REPLAY", {"DEVICE_PROOF_REPLAYED"})

    body_payload = _job_payload("body-binding")
    body_raw = _json_bytes(body_payload)
    body_headers = _proof_headers(device_private, device_id, "/v1/jobs", body_raw)
    modified_body = _json_bytes({**body_payload, "id": body_payload["id"] + "-modified"})
    body_response = session.post(
        f"{base_url}/v1/jobs",
        data=modified_body,
        headers={"Content-Type": "application/json", **auth_headers, **body_headers},
        timeout=15,
    )
    _expect_status(body_response, 403, "BODY_BINDING")

    query_payload = _job_payload("query-binding")
    query_raw = _json_bytes(query_payload)
    query_headers = _proof_headers(device_private, device_id, "/v1/jobs?probe=A", query_raw)
    query_response = session.post(
        f"{base_url}/v1/jobs?probe=B",
        data=query_raw,
        headers={"Content-Type": "application/json", **auth_headers, **query_headers},
        timeout=15,
    )
    _expect_status(query_response, 403, "QUERY_BINDING")

    api_key = os.environ.get("RD_API_KEY", "").strip()
    if not api_key:
        _fail("RD_API_KEY is required for API key bypass E2E")
    api_response, _, _ = _job_request(
        session,
        base_url,
        {"X-API-Key": api_key},
        not_activated_id,
        not_activated_private,
        _job_payload("api-key-bypass"),
    )
    _expect_status(api_response, 403, "API_KEY_BYPASS", {"DEVICE_NOT_ACTIVATED"})

    vip_response, _, _ = _job_request(
        session,
        base_url,
        auth_headers,
        not_activated_id,
        not_activated_private,
        _job_payload("vip-bypass"),
    )
    _expect_status(vip_response, 403, "VIP_BYPASS", {"DEVICE_NOT_ACTIVATED"})

    card_activate = {
        "card_code": legacy_card,
        "device_id": not_activated_id,
        "device_key_algorithm": "ED25519",
        "device_public_key": not_activated_public,
    }
    card_activate["proof"] = activation_proof(
        not_activated_private,
        audience="rd",
        license_key=legacy_card,
        device_id=not_activated_id,
        public_key_b64=card_activate["device_public_key"],
    )
    card_response = session.post(
        f"{base_url}/v1/auth/redeem",
        data=_json_bytes(card_activate),
        headers={"Content-Type": "application/json", **auth_headers},
        timeout=15,
    )
    if card_response.status_code == 200:
        _fail("CARDKEY_BYPASS was accepted")
    _pass("CARDKEY_BYPASS")
    _assert_legacy_card_unused(legacy_card, database)

    tenant_payload = _job_payload("tenant-isolation")
    tenant_target = "/v1/jobs?service_id=sx&tenant_id=sx"
    tenant_response, _, _ = _job_request(
        session,
        base_url,
        auth_headers,
        device_id,
        device_private,
        tenant_payload,
        actual_target=tenant_target,
        signed_target=tenant_target,
    )
    _expect_status(tenant_response, 200, "TENANT_ISOLATION")

    ttl = max(1, int(os.environ.get("LICENSE_CACHE_TTL_SECONDS", "30")))
    cache_response, _, _ = _job_request(
        session, base_url, auth_headers, device_id, device_private, _job_payload("cache-remote")
    )
    _expect_status(cache_response, 200, "CACHE_REMOTE")
    _compose_command("stop")
    cache_hit_response, _, _ = _job_request(
        session, base_url, auth_headers, device_id, device_private, _job_payload("cache-hit")
    )
    _expect_status(cache_hit_response, 200, "CACHE_HIT")
    time.sleep(ttl + 1)
    down_response, _, _ = _job_request(
        session, base_url, auth_headers, device_id, device_private, _job_payload("service-down")
    )
    _expect_status(down_response, 503, "SERVICE_DOWN")
    _compose_command("start")
    _wait_license_ready(license_base_url)
    recovered_response, _, _ = _job_request(
        session,
        base_url,
        auth_headers,
        device_id,
        device_private,
        _job_payload("service-recovered"),
    )
    _expect_status(recovered_response, 200, "SERVICE_RECOVERED")
    _pass("CACHE")

    # T13 background automation: the PUT and scan are real RD HTTP requests.
    # The local JSON edits below only make an existing real discovery item a
    # deterministic fixture; entitlement authorization still traverses the
    # RD service credential -> License Service HTTP -> PostgreSQL path.
    revoked_id = os.environ.get("RD_REVOKED_LICENSE_ID", "").strip()
    expired_id = os.environ.get("RD_EXPIRED_LICENSE_ID", "").strip()
    if not revoked_id or not expired_id:
        _fail("RD_REVOKED_LICENSE_ID and RD_EXPIRED_LICENSE_ID are required")
    automation_config = {
        "enabled": False,
        "auto_enqueue": True,
        "interval_seconds": 30,
        "scan_limit": 1,
        "max_auto_enqueue_per_scan": 1,
        "quality": "1080p",
    }
    automation_put = _automation_request(
        session,
        base_url,
        auth_headers,
        "/v1/automation/hongguo-new",
        device_id,
        device_private,
        automation_config,
        method="PUT",
    )
    if automation_put.status_code != 200:
        _fail(
            "BACKGROUND_ACTIVE automation save failed: "
            f"HTTP {automation_put.status_code} detail={automation_put.text}"
        )
    if automation_put.json().get("license_context_status") != "READY":
        _fail("BACKGROUND_ACTIVE did not report READY license context")
    _pass("BACKGROUND_DEVICE_BINDING")

    baseline = _automation_request(
        session,
        base_url,
        auth_headers,
        "/v1/automation/hongguo-new/scan",
        device_id,
        device_private,
    )
    if baseline.status_code != 200:
        _fail("BACKGROUND_ACTIVE baseline scan failed")
    before_background_jobs = int(baseline.json().get("total_enqueued_count") or 0)
    automation_config["scan_limit"] = 10
    active_config = _automation_request(
        session,
        base_url,
        auth_headers,
        "/v1/automation/hongguo-new",
        device_id,
        device_private,
        automation_config,
        method="PUT",
    )
    if active_config.status_code != 200:
        _fail("BACKGROUND_ACTIVE scan-limit update failed")
    active_scan = _automation_request(
        session,
        base_url,
        auth_headers,
        "/v1/automation/hongguo-new/scan",
        device_id,
        device_private,
    )
    if active_scan.status_code != 200:
        _fail("BACKGROUND_ACTIVE scan failed")
    active_status = active_scan.json()
    if int(active_status.get("total_enqueued_count") or 0) <= before_background_jobs:
        _fail("BACKGROUND_ACTIVE did not create a Job")
    background_total = int(active_status.get("total_enqueued_count") or 0)
    _pass("BACKGROUND_ACTIVE")

    # Legacy policy fixture is checked while the device is still ACTIVE so the
    # foreground scan guard can pass; the background executor must still deny
    # the missing saved context after RD reloads the persisted JSON.
    _mutate_automation_fixture(
        user_id,
        enabled=False,
        license_device_id=None,
        baseline_initialized=True,
        known_ids=[],
        last_scan_at="",
        last_error="",
    )
    _restart_rd_for_fixture()
    legacy_scan = _automation_request(
        session,
        base_url,
        auth_headers,
        "/v1/automation/hongguo-new/scan",
        device_id,
        device_private,
    )
    if legacy_scan.status_code != 200:
        _fail("LEGACY background scan request failed")
    legacy_status = legacy_scan.json()
    if legacy_status.get("license_context_status") != "REAUTH_REQUIRED":
        _fail("LEGACY automation did not require reauthorization")
    if legacy_status.get("last_error") != "BACKGROUND_LICENSE_CONTEXT_REQUIRED":
        _fail("LEGACY automation did not fail closed")
    if int(legacy_status.get("total_enqueued_count") or 0) != background_total:
        _fail("LEGACY automation created a Job")
    _pass("BACKGROUND_LEGACY_REAUTH_REQUIRED")

    # Re-authorize the same persisted policy through the normal Device-Proof
    # path before testing scheduler denial/recovery states.
    restore_put = _automation_request(
        session,
        base_url,
        auth_headers,
        "/v1/automation/hongguo-new",
        device_id,
        device_private,
        automation_config,
        method="PUT",
    )
    if restore_put.status_code != 200:
        _fail("background policy restore after legacy fixture failed")

    quota_limit = int(os.environ.get("RD_E2E_QUOTA_LIMIT", "50"))
    with sqlite3.connect(database) as connection:
        day = datetime.now(UTC).strftime("%Y-%m-%d")
        connection.execute(
            "insert into usage_daily(user_id,day,job_count) values(?,?,?) "
            "on conflict(user_id,day) do update set job_count=excluded.job_count",
            (user_id, day, quota_limit),
        )
        connection.commit()
    quota_response, _, _ = _job_request(
        session, base_url, auth_headers, device_id, device_private, _job_payload("quota")
    )
    _expect_status(quota_response, 429, "QUOTA")

    # Enable the periodic worker so revoked/expired/service-down checks do not
    # depend on a live client Device Proof while the License Service is down.
    automation_config["scan_limit"] = 50
    automation_config["enabled"] = True
    enabled_put = _automation_request(
        session,
        base_url,
        auth_headers,
        "/v1/automation/hongguo-new",
        device_id,
        device_private,
        automation_config,
        method="PUT",
    )
    if enabled_put.status_code != 200:
        _fail("background scheduler enable failed")

    time.sleep(ttl + 1)
    _rebind_prepared_license(revoked_id, device_public)
    revoked_background = _wait_background_status(
        session,
        base_url,
        auth_headers,
        expected_error="LICENSE_REVOKED",
    )
    if int(revoked_background.get("total_enqueued_count") or 0) != background_total:
        _fail("BACKGROUND_REVOKED created a Job")
    _pass("BACKGROUND_REVOKED")

    _rebind_prepared_license(expired_id, device_public)
    expired_background = _wait_background_status(
        session,
        base_url,
        auth_headers,
        expected_error="LICENSE_EXPIRED",
    )
    if int(expired_background.get("total_enqueued_count") or 0) != background_total:
        _fail("BACKGROUND_EXPIRED created a Job")
    _pass("BACKGROUND_EXPIRED")

    _set_device_identity_status(device_public, "REVOKED")
    device_revoked_background = _wait_background_status(
        session,
        base_url,
        auth_headers,
        expected_error="DEVICE_REVOKED",
    )
    if int(device_revoked_background.get("total_enqueued_count") or 0) != background_total:
        _fail("BACKGROUND_DEVICE_REVOKED created a Job")
    _pass("BACKGROUND_DEVICE_REVOKED")
    _set_device_identity_status(device_public, "ACTIVE")

    _compose_command("stop")
    try:
        service_down_background = _wait_background_status(
            session,
            base_url,
            auth_headers,
            expected_error="UNKNOWN",
            timeout=45,
        )
        if int(service_down_background.get("total_enqueued_count") or 0) != background_total:
            _fail("BACKGROUND_SERVICE_DOWN created a Job")
    finally:
        _compose_command("start")
        _wait_license_ready(license_base_url)
    _pass("BACKGROUND_SERVICE_DOWN")

    time.sleep(35)
    recovered_background = session.get(
        f"{base_url}/v1/automation/hongguo-new",
        headers=auth_headers,
        timeout=15,
    )
    if recovered_background.status_code != 200:
        _fail("BACKGROUND_SERVICE_RECOVERED status request failed")
    if recovered_background.json().get("last_error") == "UNKNOWN":
        _fail("BACKGROUND_SERVICE_RECOVERED remained fail-closed after recovery")
    _pass("BACKGROUND_SERVICE_RECOVERED")

    time.sleep(ttl + 1)
    _rebind_prepared_license(revoked_id, device_public)
    revoked_response, _, _ = _job_request(
        session,
        base_url,
        auth_headers,
        device_id,
        device_private,
        _job_payload("revoked"),
    )
    _expect_status(revoked_response, 403, "REVOKED", {"LICENSE_REVOKED"})

    _rebind_prepared_license(expired_id, device_public)
    expired_response, _, _ = _job_request(
        session,
        base_url,
        auth_headers,
        device_id,
        device_private,
        _job_payload("expired"),
    )
    _expect_status(expired_response, 403, "EXPIRED", {"LICENSE_EXPIRED"})

    print("RD LICENSE INTEGRATION PASS")
    print("CLIENT CUTOVER COMPLETE (legacy HTTP regression harness)")


if __name__ == "__main__":
    main()
