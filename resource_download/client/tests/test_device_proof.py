from __future__ import annotations

import io
import hashlib
import json
import sys
import urllib.error
from pathlib import Path

import pytest

from client.desktop.device_identity import (
    DeviceIdentityInvalid,
    DeviceIdentityManager,
    MemoryIdentityStore,
    WindowsDpapiIdentityStore,
)
from client.desktop.device_proof import DeviceProofService
from client.desktop.http_client import DesktopHttpClient, is_protected_endpoint, normalize_reason
from license_service_client.signing import (
    canonical_activation_proof,
    canonical_device_proof,
    b64u_decode,
    verify_device_signature,
)


def _headers(request) -> dict[str, str]:
    return {key.lower(): value for key, value in request.header_items()}


class _Response:
    status = 200

    def __init__(self, payload: dict):
        self._content = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return self._content


def test_first_run_and_restart_keep_one_identity() -> None:
    store = MemoryIdentityStore()
    first = DeviceIdentityManager(store).load_or_create()
    second = DeviceIdentityManager(store).load_or_create()

    assert first.device_id.startswith("dev_")
    assert first.device_id == second.device_id
    assert first.public_key == second.public_key
    assert first.private_key == second.private_key


def test_windows_dpapi_store_round_trip(tmp_path: Path) -> None:
    store = WindowsDpapiIdentityStore(tmp_path / "device_identity.dpapi")
    if sys.platform != "win32":
        pytest.skip("Windows DPAPI test")
    first = DeviceIdentityManager(store).load_or_create()
    second = DeviceIdentityManager(store).load_or_create()
    assert first.device_id == second.device_id
    assert store.path.read_bytes() != first.private_key.encode("utf-8")


def test_device_id_is_derived_from_public_key_and_corruption_fails_closed() -> None:
    store = MemoryIdentityStore()
    identity = DeviceIdentityManager(store).load_or_create()
    assert identity.device_id == "dev_" + hashlib.sha256(b64u_decode(identity.public_key)).hexdigest()

    assert store.payload is not None
    store.payload["device_id"] = "dev_" + "0" * 64
    with pytest.raises(DeviceIdentityInvalid):
        DeviceIdentityManager(store).load_or_create()
    assert store.payload["device_id"] == "dev_" + "0" * 64


def test_activation_proof_is_formally_valid() -> None:
    manager = DeviceIdentityManager(MemoryIdentityStore())
    service = DeviceProofService(manager)
    identity = service.identity()
    proof = service.activation_proof(" rd-card-01 ")
    message = canonical_activation_proof(
        "rd",
        identity.key_algorithm,
        " rd-card-01 ",
        identity.device_id,
        identity.public_key,
        proof["timestamp"],
        proof["nonce"],
    )
    assert verify_device_signature(identity.public_key, identity.key_algorithm, message, proof["signature"])


def test_request_proof_binds_method_query_and_raw_body() -> None:
    manager = DeviceIdentityManager(MemoryIdentityStore())
    service = DeviceProofService(manager)
    identity = service.identity()
    raw_body = b'{"a":1,"b":2}'
    target = "/v1/jobs?x=1"
    proof = service.request_proof("POST", target, raw_body)

    def valid(method: str, request_target: str, body: bytes) -> bool:
        body_sha = hashlib.sha256(body).hexdigest()
        message = canonical_device_proof(
            "rd",
            identity.key_algorithm,
            method,
            request_target,
            body_sha,
            proof["timestamp"],
            proof["nonce"],
        )
        return verify_device_signature(identity.public_key, identity.key_algorithm, message, proof["signature"])

    assert valid("POST", target, raw_body)
    assert not valid("GET", target, raw_body)
    assert not valid("POST", "/v1/jobs?x=2", raw_body)
    assert not valid("POST", target, b'{"a":2,"b":2}')


def test_nonce_is_fresh_for_each_proof() -> None:
    service = DeviceProofService(DeviceIdentityManager(MemoryIdentityStore()))
    nonces = {service.request_proof("POST", "/v1/jobs", b"")["nonce"] for _ in range(20)}
    assert len(nonces) == 20


def test_protected_scope_and_unprotected_scope_are_exact() -> None:
    protected = {
        ("POST", "/v1/jobs"),
        ("POST", "/v1/jobs/batch"),
        ("POST", "/v1/jobs/queue/bulk/retry"),
        ("POST", "/v1/jobs/job-1/retry"),
        ("PUT", "/v1/automation/hongguo-new"),
        ("POST", "/v1/automation/hongguo-new/scan"),
    }
    for method, target in protected:
        assert is_protected_endpoint(method, target)
    for method, target in {
        ("POST", "/v1/auth/login"),
        ("POST", "/v1/auth/redeem"),
        ("GET", "/v1/jobs"),
        ("GET", "/v1/jobs/job-1"),
        ("GET", "/v1/search?q=x"),
        ("GET", "/v1/detail?id=x"),
        ("GET", "/v1/files"),
        ("GET", "/health"),
    }:
        assert not is_protected_endpoint(method, target)


def test_http_layer_signs_protected_request_but_not_unprotected(monkeypatch) -> None:
    service = DeviceProofService(DeviceIdentityManager(MemoryIdentityStore()))
    client = DesktopHttpClient("https://rd.example", service, max_retries=0)
    calls = []

    def fake_urlopen(request, timeout=0):  # noqa: ARG001
        calls.append(request)
        return _Response({"ok": True})

    monkeypatch.setattr("client.desktop.http_client.urllib.request.urlopen", fake_urlopen)
    client.request_json("POST", "/v1/jobs?x=1", '{"a":1}', protected=True)
    client.request_json("GET", "/v1/search?q=x", b"", protected=False)
    signed = _headers(calls[0])
    unsigned = _headers(calls[1])
    assert "x-device-id" in signed
    assert "x-device-proof-signature" in signed
    assert "x-device-id" not in unsigned


def test_http_retry_regenerates_proof(monkeypatch) -> None:
    service = DeviceProofService(DeviceIdentityManager(MemoryIdentityStore()))
    client = DesktopHttpClient("https://rd.example", service, max_retries=1)
    calls = []

    def fake_urlopen(request, timeout=0):  # noqa: ARG001
        calls.append(request)
        if len(calls) == 1:
            raise urllib.error.HTTPError(
                request.full_url,
                503,
                "temporarily unavailable",
                {},
                io.BytesIO(b'{"detail":"LICENSE_SERVICE_UNAVAILABLE"}'),
            )
        return _Response({"retry": "ok"})

    monkeypatch.setattr("client.desktop.http_client.urllib.request.urlopen", fake_urlopen)
    assert client.request_json("POST", "/v1/jobs", '{"a":1}', protected=True) == {"retry": "ok"}
    first = _headers(calls[0])
    second = _headers(calls[1])
    assert first["x-device-proof-nonce"] != second["x-device-proof-nonce"]
    assert first["x-device-proof-signature"] != second["x-device-proof-signature"]


def test_error_mapping_and_browser_boundary_are_fail_closed() -> None:
    assert normalize_reason(403, "INVALID_DEVICE_PROOF") == "DEVICE_PROOF_INVALID"
    assert normalize_reason(503, "traceback should not escape") == "LICENSE_SERVICE_UNAVAILABLE"
    app_js = Path(__file__).parents[1].joinpath("ui", "app.js").read_text(encoding="utf-8")
    assert "DESKTOP_DEVICE_IDENTITY_REQUIRED" in app_js
    assert "localStorage.setItem(\"device" not in app_js
    assert "sessionStorage.setItem(\"device" not in app_js
