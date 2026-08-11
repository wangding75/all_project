#!/usr/bin/env python3
"""T16 real background entitlement E2E.

The runner uses the normal RD HTTP API and the running License Service.  Only
the RD subprocess is started with the process-local deterministic Hongguo
adapter from ``t16_deterministic_discovery_server.py``; no production module or
License Service source is changed.  Fixture preparation (fresh RD user,
official License Service Admin key generation, and persisted monitor reset)
does not replace any authorization decision.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import requests
from license_service_client import activation_proof, generate_device_identity, request_proof


ROOT = Path(__file__).resolve().parents[1]
LS_ROOT = Path(os.environ.get("LICENSE_SERVICE_ROOT", r"D:\github\license_service"))
LS_ENV_FILE = Path(
    os.environ.get("LICENSE_SERVICE_ENV_FILE", str(LS_ROOT / ".env.e2e.local"))
)
LS_HANDOFF = Path(
    os.environ.get(
        "LICENSE_SERVICE_HANDOFF", str(LS_ROOT / "data" / "e2e" / "rd-e2e.ps1")
    )
)
LS_URL = "http://127.0.0.1:18081"
RD_PORT = int(os.environ.get("T16_RD_PORT", "8001"))
RD_URL = f"http://127.0.0.1:{RD_PORT}"
COMPOSE_FILES = (
    "--env-file",
    str(LS_ENV_FILE),
    "-f",
    "docker-compose.yml",
    "-f",
    "docker-compose.e2e.yml",
)
UTC = timezone.utc


def _parse_key_value_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key and all(ch.isalnum() or ch == "_" for ch in key):
            values[key] = value
    return values


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _detail(response: requests.Response) -> str:
    try:
        return str(response.json().get("detail") or "")
    except (ValueError, AttributeError):
        return ""


def _totp(secret: str, timestamp: int | None = None) -> str:
    timestamp = int(time.time()) if timestamp is None else int(timestamp)
    padding = "=" * (-len(secret) % 8)
    key = base64.b32decode(secret + padding, casefold=True)
    counter = timestamp // 30
    digest = hmac.new(key, counter.to_bytes(8, "big"), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (int.from_bytes(digest[offset : offset + 4], "big") & 0x7FFFFFFF) % 1_000_000
    return f"{value:06d}"


class T16E2E:
    def __init__(self) -> None:
        if not LS_HANDOFF.is_file() or not LS_ENV_FILE.is_file():
            raise RuntimeError("T10/T13 License Service E2E handoff is missing")
        self.handoff = _parse_key_value_file(LS_HANDOFF)
        self.license_env = _parse_key_value_file(LS_ENV_FILE)
        if self.handoff.get("LICENSE_SERVICE_BASE_URL", "").rstrip("/") != LS_URL:
            raise RuntimeError("License Service handoff does not target 127.0.0.1:18081")
        required = (
            "LICENSE_SERVICE_BASE_URL",
            "LICENSE_SERVICE_KEY_ID",
            "LICENSE_SERVICE_PRIVATE_KEY",
            "LICENSE_SERVICE_AUDIENCE",
        )
        missing = [name for name in required if not self.handoff.get(name, "").strip()]
        if missing:
            raise RuntimeError("License Service handoff is incomplete")

        self.sensitive: set[str] = {
            self.handoff[name]
            for name in ("RD_LICENSE_KEY", "LICENSE_SERVICE_PRIVATE_KEY")
            if self.handoff.get(name)
        }
        self.sensitive.update(
            self.license_env[name]
            for name in (
                "LICENSE_MASTER_KEY",
                "POSTGRES_PASSWORD",
                "LICENSE_CONTROL_OWNER_PASSWORD",
                "LICENSE_CONTROL_DB_PASSWORD",
            )
            if self.license_env.get(name)
        )
        self.temp_dir = Path(tempfile.mkdtemp(prefix="t16-background-", dir=ROOT / "tmp"))
        self.data_dir = self.temp_dir / "rd-data"
        self.server_log = self.temp_dir / "rd-server.log"
        self.rd_process: subprocess.Popen[str] | None = None
        self.rd_log_handle = None
        self.admin = requests.Session()
        self.admin_service_id = ""
        self.admin_csrf = ""
        self.session = requests.Session()
        self.token = ""
        self.user_id = 0
        self.username = f"t16_bg_{secrets.token_hex(5)}"
        self.password = f"T16-{secrets.token_urlsafe(18)}"
        self.jwt_secret = secrets.token_hex(32)
        self.device_private_keys: list[str] = []
        self.proof_signatures: list[str] = []
        self.current_device_id = ""
        self.current_device_private_key = ""
        self.current_license_id = ""
        self.candidate_count = 0
        self.active_jobs = 0
        self.active_quota = 0

    @property
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    @property
    def policy_path(self) -> Path:
        return self.data_dir / "automation" / "hongguo_monitors.json"

    @property
    def database_path(self) -> Path:
        return self.data_dir / "app.db"

    def _compose(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["LICENSE_HOST_PORT"] = "18081"
        result = subprocess.run(
            ["docker", "compose", *COMPOSE_FILES, *args],
            cwd=LS_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"License Service lifecycle command failed: {args[0]}")
        return result

    def ensure_license_ready(self) -> None:
        response = requests.get(f"{LS_URL}/health/ready", timeout=5)
        if response.status_code != 200:
            raise RuntimeError("License Service readiness failed")
        ps = self._compose("ps", "-q", "postgres")
        container = ps.stdout.strip().splitlines()[-1] if ps.stdout.strip() else ""
        if not container:
            raise RuntimeError("PostgreSQL container is missing")
        health = subprocess.run(
            ["docker", "inspect", "--format", "{{if .State.Health}}{{.State.Health.Status}}{{end}}", container],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        ).stdout.strip()
        if health != "healthy":
            raise RuntimeError("PostgreSQL is not healthy")

    def stop_license_service(self) -> None:
        self._compose("stop", "license-service")

    def start_license_service(self) -> None:
        self._compose("start", "license-service")
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try:
                if requests.get(f"{LS_URL}/health/ready", timeout=3).status_code == 200:
                    return
            except requests.RequestException:
                pass
            time.sleep(2)
        raise RuntimeError("License Service did not recover")

    def bootstrap_admin(self) -> None:
        admin_password = f"T16-admin-{secrets.token_urlsafe(20)}"
        admin_username = f"t16_admin_{secrets.token_hex(5)}"
        result = self._compose(
            "exec",
            "-T",
            "-e",
            f"LICENSE_ADMIN_BOOTSTRAP_PASSWORD={admin_password}",
            "license-service",
            "python",
            "scripts/bootstrap_admin.py",
            "--username",
            admin_username,
        )
        totp_secret = ""
        for line in result.stdout.splitlines():
            if line.startswith("TOTP_SECRET="):
                totp_secret = line.split("=", 1)[1].strip()
                break
        if not totp_secret:
            raise RuntimeError("License Service Admin bootstrap did not return a TOTP seed")

        response = self.admin.post(
            f"{LS_URL}/admin/api/login",
            json={
                "username": admin_username,
                "password": admin_password,
                "totp_code": _totp(totp_secret),
            },
            timeout=15,
        )
        if response.status_code != 200:
            raise RuntimeError("License Service Admin login failed")
        session = self.admin.get(f"{LS_URL}/admin/api/session", timeout=15)
        if session.status_code != 200:
            raise RuntimeError("License Service Admin session failed")
        self.admin_csrf = str(session.json().get("csrf_token") or "")
        services = self.admin.get(f"{LS_URL}/admin/api/services", timeout=15)
        if services.status_code != 200:
            raise RuntimeError("License Service service listing failed")
        rd = next((row for row in services.json() if row.get("code") == "rd"), None)
        if not rd or not rd.get("id"):
            raise RuntimeError("RD tenant service is missing")
        self.admin_service_id = str(rd["id"])
        if os.environ.get("T16_ROTATE_RD_CREDENTIAL", "").strip().lower() == "true":
            rotated = self._admin(
                "POST",
                f"/admin/api/services/{self.admin_service_id}/rotate-key?grace_seconds=0",
            )
            if rotated.status_code != 200:
                raise RuntimeError("RD service credential rotation failed")
            credential = rotated.json()
            key_id = str(credential.get("key_id") or "")
            private_key = str(credential.get("service_private_key") or "")
            if not key_id or not private_key:
                raise RuntimeError("RD service credential rotation returned incomplete material")
            self.handoff["LICENSE_SERVICE_KEY_ID"] = key_id
            self.handoff["LICENSE_SERVICE_PRIVATE_KEY"] = private_key
            self.sensitive.update({key_id, private_key})

    def _admin(self, method: str, target: str, **kwargs: Any) -> requests.Response:
        headers = dict(kwargs.pop("headers", {}) or {})
        if method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
            headers["x-csrf-token"] = self.admin_csrf
        response = self.admin.request(method, f"{LS_URL}{target}", headers=headers, timeout=20, **kwargs)
        return response

    def ensure_plan(self) -> str:
        response = self._admin("GET", f"/admin/api/services/{self.admin_service_id}/plans")
        if response.status_code != 200:
            raise RuntimeError("RD plan listing failed")
        plan = next((row for row in response.json() if row.get("code") == "RD_E2E_DAY"), None)
        if plan is None:
            created = self._admin(
                "POST",
                f"/admin/api/services/{self.admin_service_id}/plans",
                json={
                    "code": "RD_E2E_DAY",
                    "name": "RD T16 deterministic E2E day",
                    "duration_value": 1,
                    "duration_unit": "DAY",
                    "max_devices": 1,
                },
            )
            if created.status_code != 200:
                raise RuntimeError("RD_E2E_DAY plan provisioning failed")
            plan = created.json()
        plan_id = str(plan.get("id") or "")
        if not plan_id:
            raise RuntimeError("RD_E2E_DAY plan id is missing")
        return plan_id

    def generate_keys(self, count: int = 2) -> list[str]:
        plan_id = self.ensure_plan()
        response = self._admin(
            "POST",
            f"/admin/api/services/{self.admin_service_id}/keys/generate",
            json={
                "plan_id": plan_id,
                "count": count,
                "batch_code": f"T16-{secrets.token_hex(5)}",
                "prefix": "T16",
            },
        )
        if response.status_code != 200:
            raise RuntimeError("RD_E2E_DAY license key generation failed")
        keys = [str(value) for value in response.json().get("keys") or []]
        if len(keys) != count:
            raise RuntimeError("RD E2E key generation returned an unexpected count")
        self.sensitive.update(keys)
        return keys

    def list_licenses(self) -> list[dict[str, Any]]:
        response = self._admin(
            "GET",
            f"/admin/api/services/{self.admin_service_id}/licenses",
        )
        if response.status_code != 200:
            raise RuntimeError("RD license listing failed")
        return list(response.json())

    def revoke_license(self, license_id: str) -> None:
        response = self._admin(
            "POST",
            f"/admin/api/services/{self.admin_service_id}/licenses/{license_id}/revoke",
            json={"reason": "T16_BACKGROUND_REVOKE"},
        )
        if response.status_code != 200:
            raise RuntimeError("RD license revoke failed")

    def start_rd(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update(
            {
                "PYTHONPATH": str(ROOT / "server"),
                "RESOURCE_DOWNLOAD_ROOT": str(ROOT),
                "HOST": "127.0.0.1",
                "PORT": str(RD_PORT),
                "AUTH_MODE": "jwt_only",
                "JWT_SECRET": self.jwt_secret,
                "DATA_DIR": str(self.data_dir),
                "API_KEY": secrets.token_urlsafe(32),
                "FREE_JOBS_PER_DAY": "0",
                "VIP_JOBS_PER_DAY": "50",
                "MAX_CONCURRENT_JOBS": "1",
                "MAX_QUEUED_JOBS": "50",
                "PLATFORM_PROBE_ON_STARTUP": "false",
                "FANQIE_PROBE_ON_STARTUP": "false",
                "FANQIE_TRY_START_AGENT": "false",
                "TRY_START_PLATFORM_APPS": "false",
                "REQUIRE_PLATFORM_APPS": "false",
                "LICENSE_SERVICE_BASE_URL": self.handoff["LICENSE_SERVICE_BASE_URL"],
                "LICENSE_SERVICE_KEY_ID": self.handoff["LICENSE_SERVICE_KEY_ID"],
                "LICENSE_SERVICE_PRIVATE_KEY": self.handoff["LICENSE_SERVICE_PRIVATE_KEY"],
                "LICENSE_SERVICE_AUDIENCE": self.handoff.get("LICENSE_SERVICE_AUDIENCE", "rd"),
                "LICENSE_CACHE_TTL_SECONDS": self.handoff.get("LICENSE_CACHE_TTL_SECONDS", "30"),
                "LICENSE_SERVICE_TIMEOUT": self.handoff.get("LICENSE_SERVICE_TIMEOUT", "3"),
                "LICENSE_SERVICE_VERIFY": self.handoff.get("LICENSE_SERVICE_VERIFY", "false"),
                "LICENSE_SERVICE_CA_BUNDLE": self.handoff.get("LICENSE_SERVICE_CA_BUNDLE", ""),
                "LICENSE_SERVICE_CLIENT_CERT": self.handoff.get("LICENSE_SERVICE_CLIENT_CERT", ""),
                "LICENSE_SERVICE_CLIENT_KEY": self.handoff.get("LICENSE_SERVICE_CLIENT_KEY", ""),
            }
        )
        self.rd_log_handle = self.server_log.open("a", encoding="utf-8")
        self.rd_process = subprocess.Popen(
            [sys.executable, "-u", str(ROOT / "scripts" / "t16_deterministic_discovery_server.py")],
            cwd=ROOT,
            env=env,
            stdout=self.rd_log_handle,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.wait_rd_ready()

    def stop_rd(self) -> None:
        process = self.rd_process
        self.rd_process = None
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        if self.rd_log_handle is not None:
            self.rd_log_handle.close()
            self.rd_log_handle = None

    def restart_rd(self) -> None:
        self.stop_rd()
        time.sleep(1)
        self.start_rd()

    def wait_rd_ready(self) -> None:
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                if requests.get(f"{RD_URL}/health", timeout=3).status_code == 200:
                    return
            except requests.RequestException:
                pass
            if self.rd_process is not None and self.rd_process.poll() is not None:
                raise RuntimeError("deterministic RD server exited during startup")
            time.sleep(1)
        raise RuntimeError("deterministic RD server did not become ready")

    def register_and_login(self) -> None:
        register = self.session.post(
            f"{RD_URL}/v1/auth/register",
            json={"username": self.username, "password": self.password},
            timeout=15,
        )
        if register.status_code != 201:
            raise RuntimeError("T16 RD user registration failed")
        login = self.session.post(
            f"{RD_URL}/v1/auth/login",
            json={"username": self.username, "password": self.password},
            timeout=15,
        )
        if login.status_code != 200:
            raise RuntimeError("T16 RD user login failed")
        self.token = str(login.json().get("access_token") or "")
        if not self.token:
            raise RuntimeError("T16 RD JWT is missing")
        me = self.session.get(f"{RD_URL}/v1/auth/me", headers=self.auth_headers, timeout=15)
        if me.status_code != 200:
            raise RuntimeError("T16 RD identity lookup failed")
        self.user_id = int(me.json()["id"])

    def activate(self, license_key: str) -> tuple[str, str, str, str]:
        before = {str(row.get("id")) for row in self.list_licenses()}
        device_id, private_key, public_key = generate_device_identity()
        self.device_private_keys.append(private_key)
        self.current_device_id = device_id
        self.current_device_private_key = private_key
        proof = activation_proof(
            private_key,
            audience="rd",
            license_key=license_key,
            device_id=device_id,
            public_key_b64=public_key,
        )
        self.proof_signatures.append(str(proof.get("signature") or ""))
        payload = {
            "card_code": license_key,
            "device_id": device_id,
            "device_key_algorithm": "ED25519",
            "device_public_key": public_key,
            "proof": proof,
        }
        response = self.session.post(
            f"{RD_URL}/v1/auth/redeem",
            data=_json_bytes(payload),
            headers={"Content-Type": "application/json", **self.auth_headers},
            timeout=20,
        )
        if response.status_code != 200 or not response.json().get("success"):
            raise RuntimeError("T16 RD activation failed")
        deadline = time.monotonic() + 20
        license_id = ""
        while time.monotonic() < deadline:
            rows = self.list_licenses()
            new_rows = [row for row in rows if str(row.get("id")) not in before]
            if new_rows:
                license_id = str(new_rows[0].get("id") or "")
                break
            time.sleep(1)
        if not license_id:
            raise RuntimeError("activated License Service license was not visible to Admin API")
        self.current_license_id = license_id
        return device_id, private_key, public_key, license_id

    def _signed_headers(
        self,
        method: str,
        target: str,
        raw_body: bytes = b"",
        *,
        device_id: str,
        private_key: str,
    ) -> dict[str, str]:
        proof = request_proof(
            private_key,
            audience="rd",
            method=method,
            request_target=target,
            body_sha256=hashlib.sha256(raw_body).hexdigest(),
        )
        self.proof_signatures.append(str(proof.get("signature") or ""))
        return {
            "X-Device-Id": device_id,
            "X-Device-Key-Algorithm": "ED25519",
            "X-Device-Proof-Timestamp": str(proof["timestamp"]),
            "X-Device-Proof-Nonce": str(proof["nonce"]),
            "X-Device-Proof-Signature": str(proof["signature"]),
        }

    def configure(
        self,
        device_id: str,
        private_key: str,
        *,
        enabled: bool,
    ) -> dict[str, Any]:
        target = "/v1/automation/hongguo-new"
        payload = {
            "enabled": enabled,
            "auto_enqueue": True,
            "interval_seconds": 30,
            "scan_limit": 1,
            "max_auto_enqueue_per_scan": 1,
            "quality": "1080p",
            "concurrency": 1,
        }
        raw = _json_bytes(payload)
        response = self.session.put(
            f"{RD_URL}{target}",
            data=raw,
            headers={
                "Content-Type": "application/json",
                **self.auth_headers,
                **self._signed_headers("PUT", target, raw, device_id=device_id, private_key=private_key),
            },
            timeout=20,
        )
        if response.status_code != 200:
            raise RuntimeError(f"automation configuration failed: HTTP {response.status_code}")
        return response.json()

    def scan_now(self, device_id: str, private_key: str) -> dict[str, Any]:
        target = "/v1/automation/hongguo-new/scan"
        response = self.session.post(
            f"{RD_URL}{target}",
            data=b"",
            headers={
                **self.auth_headers,
                **self._signed_headers("POST", target, device_id=device_id, private_key=private_key),
            },
            timeout=20,
        )
        if response.status_code != 200:
            raise RuntimeError(f"baseline scan failed: HTTP {response.status_code}")
        return response.json()

    def status(self) -> dict[str, Any]:
        target = "/v1/automation/hongguo-new"
        response = self.session.get(
            f"{RD_URL}{target}",
            headers={
                **self.auth_headers,
                **self._signed_headers(
                    "GET",
                    target,
                    device_id=self.current_device_id,
                    private_key=self.current_device_private_key,
                ),
            },
            timeout=15,
        )
        if response.status_code != 200:
            raise RuntimeError(f"automation status failed: HTTP {response.status_code}")
        return response.json()

    def jobs_total(self) -> int:
        target = "/v1/jobs?page=1&page_size=100"
        response = self.session.get(
            f"{RD_URL}{target}",
            headers={
                **self.auth_headers,
                **self._signed_headers(
                    "GET",
                    target,
                    device_id=self.current_device_id,
                    private_key=self.current_device_private_key,
                ),
            },
            timeout=15,
        )
        if response.status_code != 200:
            raise RuntimeError("RD job listing failed")
        return int(response.json().get("total") or 0)

    def quota_count(self) -> int:
        target = "/v1/license/status"
        response = self.session.get(
            f"{RD_URL}{target}",
            headers={
                **self.auth_headers,
                **self._signed_headers(
                    "GET",
                    target,
                    device_id=self.current_device_id,
                    private_key=self.current_device_private_key,
                ),
            },
            timeout=15,
        )
        if response.status_code != 200:
            raise RuntimeError("RD quota lookup failed")
        return int(response.json().get("used") or 0)

    def persisted_status(self) -> dict[str, Any]:
        if not self.policy_path.is_file():
            raise RuntimeError("automation fixture was not persisted")
        payload = json.loads(self.policy_path.read_text(encoding="utf-8"))
        candidates = [
            value
            for value in payload.values()
            if isinstance(value, dict)
            and value.get("owner_user_id") == self.user_id
            and value.get("license_device_id") in (None, self.current_device_id)
        ]
        if not candidates:
            raise RuntimeError("persisted automation status is missing")
        return dict(candidates[0])

    def persisted_quota_count(self) -> int:
        with sqlite3.connect(self.database_path) as db:
            row = db.execute(
                "SELECT used_count FROM license_usage_daily WHERE license_id = ?",
                (self.current_license_id,),
            ).fetchone()
        return int(row[0]) if row else 0

    def persisted_job_count(self) -> int:
        count = 0
        for path in self.data_dir.joinpath("jobs").glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if payload.get("license_id") == self.current_license_id:
                count += 1
        return count

    def assert_active_endpoints_denied(self) -> None:
        for target in ("/v1/license/status", "/v1/automation/hongguo-new", "/v1/jobs?page=1&page_size=100"):
            response = self.session.get(
                f"{RD_URL}{target}",
                headers={
                    **self.auth_headers,
                    **self._signed_headers(
                        "GET",
                        target,
                        device_id=self.current_device_id,
                        private_key=self.current_device_private_key,
                    ),
                },
                timeout=15,
            )
            if response.status_code != 403:
                raise RuntimeError(f"revoked endpoint was not denied: {target}")

    def fixture_reset(
        self,
        *,
        enabled: bool,
        license_device_id: str | None,
        baseline_initialized: bool,
        known_ids: list[str],
        last_scan_at: str = "",
        last_error: str = "",
    ) -> None:
        if not self.policy_path.is_file():
            raise RuntimeError("automation fixture was not persisted")
        payload = json.loads(self.policy_path.read_text(encoding="utf-8"))
        policy = payload.get(f"user:{self.user_id}")
        if not isinstance(policy, dict):
            candidates = [
                value
                for value in payload.values()
                if isinstance(value, dict)
                and value.get("owner_user_id") == self.user_id
                and (
                    license_device_id is None
                    or value.get("license_device_id") == license_device_id
                )
            ]
            policy = candidates[0] if candidates else None
        if not isinstance(policy, dict):
            raise RuntimeError("automation policy is missing")
        policy.update(
            {
                "enabled": enabled,
                "license_device_id": license_device_id,
                "baseline_initialized": baseline_initialized,
                "known_ids": list(known_ids),
                "last_scan_at": last_scan_at,
                "last_error": last_error,
            }
        )
        self.policy_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def wait_status(
        self,
        predicate: Callable[[dict[str, Any]], bool],
        label: str,
        *,
        timeout: float = 55,
        persisted: bool = False,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        last: dict[str, Any] = {}
        while time.monotonic() < deadline:
            last = self.persisted_status() if persisted else self.status()
            if predicate(last):
                return last
            time.sleep(2)
        raise RuntimeError(f"background state did not reach {label}")

    def reset_for_baseline(self, device_id: str) -> None:
        self.fixture_reset(
            enabled=False,
            license_device_id=device_id,
            baseline_initialized=False,
            known_ids=[],
            last_scan_at="",
            last_error="",
        )
        self.restart_rd()

    def assert_log_secrets_safe(self) -> None:
        texts: list[str] = []
        if self.server_log.is_file():
            texts.append(self.server_log.read_text(encoding="utf-8", errors="replace"))
        result = self._compose("logs", "--no-color", "license-service")
        texts.append(result.stdout)
        needles = [value for value in (*self.sensitive, *self.device_private_keys, *self.proof_signatures) if value]
        for text in texts:
            if any(needle in text for needle in needles):
                raise RuntimeError("secret or proof material appeared in an E2E log")

    def run(self) -> None:
        self.ensure_license_ready()
        self.bootstrap_admin()
        keys = self.generate_keys(2)
        self.start_rd()
        self.register_and_login()

        first_device, first_private, _first_public, first_license_id = self.activate(keys[0])
        self.configure(first_device, first_private, enabled=False)
        baseline = self.scan_now(first_device, first_private)
        if baseline.get("baseline_initialized") is not True or baseline.get("last_detected_count") != 0:
            raise RuntimeError("deterministic baseline was not established")
        self.fixture_reset(
            enabled=True,
            license_device_id=first_device,
            baseline_initialized=True,
            known_ids=[],
            last_scan_at="",
            last_error="",
        )
        jobs_before_active = self.jobs_total()
        quota_before_active = self.quota_count()
        active_status = self.restart_and_wait_active(jobs_before_active)
        self.candidate_count = int(active_status.get("last_detected_count") or 0)
        if self.candidate_count < 1:
            raise RuntimeError("deterministic discovery did not return a candidate")
        self.active_jobs = self.jobs_total()
        self.active_quota = self.quota_count()
        if self.active_jobs <= jobs_before_active or self.active_quota <= quota_before_active:
            raise RuntimeError("ACTIVE background cycle did not create and charge a Job")

        self.revoke_license(first_license_id)
        self.fixture_reset(
            enabled=True,
            license_device_id=first_device,
            baseline_initialized=True,
            known_ids=[],
            last_scan_at="",
            last_error="",
        )
        revoked_status = self.restart_and_wait_error("LICENSE_REVOKED")
        if int(revoked_status.get("last_detected_count") or 0) < 1:
            raise RuntimeError("revoke cycle did not discover a candidate")
        if int(revoked_status.get("total_enqueued_count") or 0) != int(active_status.get("total_enqueued_count") or 0):
            raise RuntimeError("LICENSE_REVOKED background cycle created a Job")
        self.assert_active_endpoints_denied()
        if self.persisted_quota_count() != self.active_quota:
            raise RuntimeError("LICENSE_REVOKED background cycle consumed quota")

        # Use a separate real RD user for service-down/recovery so a prior
        # successful Job cannot trigger the production duplicate suppression
        # rule.  The discovery candidate and all background code paths remain
        # identical.
        self.username = f"t16_bg_recovery_{secrets.token_hex(5)}"
        self.password = f"T16-{secrets.token_urlsafe(18)}"
        self.session = requests.Session()
        self.token = ""
        self.register_and_login()
        second_device, second_private, _second_public, _second_license_id = self.activate(keys[1])
        self.configure(second_device, second_private, enabled=False)
        self.reset_for_baseline(second_device)
        second_baseline = self.scan_now(second_device, second_private)
        if second_baseline.get("last_detected_count") != 0:
            raise RuntimeError("service-down baseline was not established")
        jobs_before_down = self.jobs_total()
        quota_before_down = self.quota_count()
        self.fixture_reset(
            enabled=True,
            license_device_id=second_device,
            baseline_initialized=True,
            known_ids=[],
            last_scan_at="",
            last_error="",
        )
        self.stop_license_service()
        try:
            down_status = self.restart_and_wait_error("UNKNOWN")
            if int(down_status.get("last_detected_count") or 0) < 1:
                raise RuntimeError("service-down cycle did not discover a candidate")
            try:
                if self.jobs_total() != jobs_before_down:
                    raise RuntimeError("service-down background cycle created a Job")
            except RuntimeError as exc:
                if str(exc) != "RD job listing failed":
                    raise
            if self.persisted_job_count() != jobs_before_down or self.persisted_quota_count() != quota_before_down:
                raise RuntimeError("service-down background cycle created or charged a Job")
        finally:
            self.start_license_service()
        recovered_status = self.restart_and_wait_active(jobs_before_down)
        if int(recovered_status.get("last_detected_count") or 0) < 1:
            raise RuntimeError("service recovery cycle did not discover a candidate")
        if self.jobs_total() <= jobs_before_down or self.quota_count() <= quota_before_down:
            raise RuntimeError("service recovery did not resume the active background path")

        jobs_before_legacy = self.jobs_total()
        quota_before_legacy = self.quota_count()
        self.fixture_reset(
            enabled=True,
            license_device_id=None,
            baseline_initialized=True,
            known_ids=[],
            last_scan_at="",
            last_error="",
        )
        legacy_status = self.restart_and_wait_error("BACKGROUND_LICENSE_CONTEXT_REQUIRED")
        if int(legacy_status.get("last_detected_count") or 0) < 1:
            raise RuntimeError("legacy cycle did not discover a candidate")
        if self.jobs_total() != jobs_before_legacy or self.quota_count() != quota_before_legacy:
            raise RuntimeError("legacy automation created or charged a Job")
        self.assert_log_secrets_safe()

        print("Deterministic Discovery: PASS")
        print(f"Candidate Count: {self.candidate_count}")
        print("Background ACTIVE: PASS")
        print("Background Revoke: LICENSE_REVOKED / DENIED")
        print("New Job After Revoke: 0")
        print("Quota After Revoke: UNCHANGED")
        print("Background Service Down: FAIL-CLOSED")
        print("Service Recovery: PASS")
        print("Legacy Automation: FAIL-CLOSED")
        print("Real License Service HTTP: PASS")
        print("Secrets: SAFE")

    def restart_and_wait_active(self, previous_jobs: int) -> dict[str, Any]:
        self.restart_rd()
        return self.wait_status(
            lambda status: int(status.get("last_detected_count") or 0) >= 1
            and not str(status.get("last_error") or "")
            and int(status.get("total_enqueued_count") or 0) > 0
            and self.jobs_total() > previous_jobs,
            "ACTIVE",
        )

    def restart_and_wait_error(self, error: str) -> dict[str, Any]:
        self.restart_rd()
        return self.wait_status(
            lambda status: int(status.get("last_detected_count") or 0) >= 1
            and str(status.get("last_error") or "") == error,
            error,
            persisted=True,
        )


def main() -> int:
    runner = T16E2E()
    try:
        runner.run()
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            runner.stop_rd()
        finally:
            try:
                runner.start_license_service()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
