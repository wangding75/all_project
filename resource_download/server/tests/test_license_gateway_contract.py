"""License Service SDK/cache contract tests for the RD adapter."""

from __future__ import annotations

import hashlib
import time

import httpx
from license_service_client import (
    LicenseServerClient,
    MemoryReplayStore,
    generate_device_identity,
    generate_device_keypair,
    request_proof,
)


def _sdk_client(handler, *, public_key: str, ttl: int = 30) -> LicenseServerClient:
    service_private, _service_public = generate_device_keypair()
    return LicenseServerClient(
        "https://license.test",
        "rd-service-key",
        service_private,
        audience="rd",
        cache_ttl_seconds=ttl,
        replay_store=MemoryReplayStore(max_entries=1000),
        transport=httpx.MockTransport(handler),
    )


def _request_proof(private_key: str, *, target: str, body: bytes) -> dict:
    return request_proof(
        private_key,
        audience="rd",
        method="POST",
        request_target=target,
        body_sha256=hashlib.sha256(body).hexdigest(),
    )


def test_sdk_cache_hit_still_verifies_current_proof_and_replay_guard():
    device_id, device_private, device_public = generate_device_identity()
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "activated": True,
                "reason": "ACTIVE",
                "license_id": "lic-1",
                "plan_code": "rd-pro",
                "expires_at": "2099-01-01T00:00:00+00:00",
                "device_public_key": device_public,
                "device_key_algorithm": "ED25519",
            },
            request=request,
        )

    client = _sdk_client(handler, public_key=device_public)
    try:
        raw = b'{"a":1}'
        target = "/v1/jobs?x=1"
        first = client.check_device_request(
            device_id=device_id,
            request_method="POST",
            request_target=target,
            raw_body=raw,
            device_proof=_request_proof(device_private, target=target, body=raw),
        )
        assert first["decision"] == "ACTIVE"
        assert first["source"] == "remote"

        second_proof = _request_proof(device_private, target=target, body=raw)
        cached = client.check_device_request(
            device_id=device_id,
            request_method="POST",
            request_target=target,
            raw_body=raw,
            device_proof=second_proof,
        )
        assert cached["decision"] == "ACTIVE"
        assert cached["source"] == "cache"
        assert len(calls) == 1

        replay = client.check_device_request(
            device_id=device_id,
            request_method="POST",
            request_target=target,
            raw_body=raw,
            device_proof=second_proof,
        )
        assert replay["decision"] == "INACTIVE"
        assert replay["reason"] == "DEVICE_PROOF_REPLAYED"

        changed_body = client.check_device_request(
            device_id=device_id,
            request_method="POST",
            request_target=target,
            raw_body=b'{"a":2}',
            device_proof=_request_proof(device_private, target=target, body=raw),
        )
        assert changed_body["decision"] == "INACTIVE"
        assert changed_body["reason"] == "INVALID_DEVICE_PROOF"

        changed_query = client.check_device_request(
            device_id=device_id,
            request_method="POST",
            request_target="/v1/jobs?x=2",
            raw_body=raw,
            device_proof=_request_proof(device_private, target=target, body=raw),
        )
        assert changed_query["decision"] == "INACTIVE"
        assert changed_query["reason"] == "INVALID_DEVICE_PROOF"
    finally:
        client.close()


def test_sdk_cache_expiry_rechecks_license_service():
    device_id, device_private, device_public = generate_device_identity()
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "activated": True,
                "reason": "ACTIVE",
                "expires_at": "2099-01-01T00:00:00+00:00",
                "device_public_key": device_public,
                "device_key_algorithm": "ED25519",
            },
            request=request,
        )

    client = _sdk_client(handler, public_key=device_public, ttl=1)
    try:
        raw = b"{}"
        target = "/v1/jobs"
        for _ in range(2):
            result = client.check_device_request(
                device_id=device_id,
                request_method="POST",
                request_target=target,
                raw_body=raw,
                device_proof=_request_proof(device_private, target=target, body=raw),
            )
            assert result["decision"] == "ACTIVE"
        assert len(calls) == 1
        time.sleep(1.1)
        result = client.check_device_request(
            device_id=device_id,
            request_method="POST",
            request_target=target,
            raw_body=raw,
            device_proof=_request_proof(device_private, target=target, body=raw),
        )
        assert result["source"] == "remote"
        assert len(calls) == 2
    finally:
        client.close()


def test_sdk_network_and_non_2xx_are_unknown_fail_closed():
    _device_id, _device_private, device_public = generate_device_identity()
    service_private, _ = generate_device_keypair()

    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("license timeout", request=request)

    timeout_client = LicenseServerClient(
        "https://license.test",
        "rd-service-key",
        service_private,
        audience="rd",
        transport=httpx.MockTransport(timeout_handler),
    )
    try:
        result = timeout_client.check_device_request(
            device_id="dev_" + "1" * 64,
            request_method="POST",
            request_target="/v1/jobs",
            raw_body=b"",
            device_proof={"timestamp": 1, "nonce": "nonce-1234567890", "signature": "sig"},
        )
        assert result["decision"] == "UNKNOWN"
        assert result["reason"] == "LICENSE_SERVICE_UNAVAILABLE"
    finally:
        timeout_client.close()

    def rejected_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "unavailable"}, request=request)

    rejected_client = LicenseServerClient(
        "https://license.test",
        "rd-service-key",
        service_private,
        audience="rd",
        transport=httpx.MockTransport(rejected_handler),
    )
    try:
        result = rejected_client.check_device_request(
            device_id="dev_" + "1" * 64,
            request_method="POST",
            request_target="/v1/jobs",
            raw_body=b"",
            device_proof={"timestamp": 1, "nonce": "nonce-1234567890", "signature": "sig"},
        )
        assert result["decision"] == "UNKNOWN"
        assert result["reason"] == "LICENSE_SERVICE_REJECTED"
        assert result["http_status"] == 503
    finally:
        rejected_client.close()


def test_memory_replay_store_consumes_nonce_once():
    store = MemoryReplayStore(max_entries=2)
    assert store.consume("nonce", expires_at=time.time() + 30) is True
    assert store.consume("nonce", expires_at=time.time() + 30) is False


def test_rd_license_guard_scope_covers_all_ordinary_business_routes():
    from app.main import app

    expected = {
        "/v1/search",
        "/v1/detail",
        "/v1/discover",
        "/v1/batch/resolve",
        "/v1/image/recognize",
        "/v1/hongguo/people",
        "/v1/jobs",
        "/v1/jobs/batch",
        "/v1/jobs",
        "/v1/jobs/summary",
        "/v1/jobs/queue",
        "/v1/jobs/queue/pause",
        "/v1/jobs/queue/resume",
        "/v1/jobs/queue/reorder",
        "/v1/jobs/queue/bulk",
        "/v1/jobs/queue/bulk/retry",
        "/v1/jobs/{job_id}/retry",
        "/v1/jobs/{job_id}",
        "/v1/automation/hongguo-new",
        "/v1/automation/hongguo-new/scan",
        "/v1/files",
        "/v1/files/thumbnail",
        "/v1/files/{file_id:path}",
        "/v1/files/{file_id:path}/open",
    }
    guarded = {
        route.path
        for route in app.routes
        if any(
            getattr(dependency.call, "__name__", "") == "require_active_device_license"
            for dependency in getattr(getattr(route, "dependant", None), "dependencies", [])
        )
    }
    assert expected <= guarded
