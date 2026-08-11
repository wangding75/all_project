"""T13 background automation authorization coverage."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.auth import Identity, require_identity
from app.automation.hongguo_monitor import HongguoMonitorService
from app.config import Settings, get_settings
from app.license_gateway import LicenseGateway, get_license_gateway
from app.main import app
from app.models import DiscoverItem, HongguoMonitorConfig, JobStatus, PlatformName


DEVICE_ID = "dev_" + "a" * 64


class _Gateway:
    def __init__(self, result: dict):
        self.result = dict(result)
        self.calls: list[str] = []

    def check_device_entitlement(self, device_id: str):
        self.calls.append(device_id)
        return dict(self.result)


class _Manager:
    def __init__(self, events: list[str] | None = None):
        self.jobs = []
        self.events = events if events is not None else []

    async def list_jobs_for(self, *_args, **_kwargs):
        return list(self.jobs), len(self.jobs)

    async def create_job(self, **kwargs):
        self.events.append("job")
        record = SimpleNamespace(
            job_id=f"job-{len(self.jobs) + 1}",
            platform=kwargs["platform"],
            item_id=kwargs["item_id"],
            status=JobStatus.pending,
            options=kwargs["options"],
        )
        self.jobs.append(record)
        return record


class _Platform:
    def __init__(self):
        self.rows = [
            DiscoverItem(
                id="old",
                title="old",
                platform=PlatformName.hongguo,
            )
        ]

    async def discover(self, _kind: str, *, limit: int = 50):
        return self.rows[:limit]


async def _scan_once_with_new_item(
    tmp_path,
    monkeypatch,
    result: dict,
    *,
    identity: Identity | None = None,
    policy_fields: dict | None = None,
):
    import app.automation.hongguo_monitor as monitor_module

    settings = Settings(data_dir=tmp_path, max_queued_jobs=10)
    manager = _Manager()
    gateway = _Gateway(result)
    platform = _Platform()
    monkeypatch.setattr(monitor_module, "get_platform", lambda _name: platform)
    import app.db as db_module
    import app.quota as quota_module

    class _DB:
        def query(self, *_args):
            return self

        def filter(self, *_args):
            return self

        def first(self):
            return SimpleNamespace(is_active=True)

        def close(self):
            pass

    monkeypatch.setattr(db_module, "SessionLocal", lambda: _DB())
    monkeypatch.setattr(quota_module, "check_job_quota", lambda *_args: None)
    monkeypatch.setattr(quota_module, "increment_job_quota", lambda *_args: None)
    service = HongguoMonitorService(settings, manager, gateway)
    identity = identity or Identity(kind="user", user_id=7)
    config = HongguoMonitorConfig(enabled=False, auto_enqueue=True)
    await service.configure(identity, config, verified_device_id=DEVICE_ID)
    if policy_fields:
        service._policies["ops" if identity.kind != "user" else f"user:{identity.user_id}"].update(
            policy_fields
        )
    await service.scan_now(identity)  # baseline
    platform.rows.append(
        DiscoverItem(
            id="new",
            title="new",
            platform=PlatformName.hongguo,
            extra={"episode_count": 12},
        )
    )
    status = await service.scan_now(identity)
    return service, manager, gateway, status


def test_gateway_calls_rc3_background_entitlement_method():
    class _Client:
        def __init__(self):
            self.called = []

        def check_device_entitlement(self, device_id):
            self.called.append(device_id)
            return {"decision": "INACTIVE", "reason": "LICENSE_REVOKED"}

    client = _Client()
    gateway = LicenseGateway(client=client, configured=True)
    result = gateway.check_device_entitlement(DEVICE_ID)
    assert client.called == [DEVICE_ID]
    assert result["decision"] == "INACTIVE"
    assert result["reason"] == "LICENSE_REVOKED"


def test_active_entitlement_creates_background_job(tmp_path, monkeypatch):
    service, manager, gateway, status = asyncio.run(
        _scan_once_with_new_item(
            tmp_path,
            monkeypatch,
            {"decision": "ACTIVE", "reason": "ACTIVE"},
        )
    )
    assert status.license_context_status == "READY"
    assert len(manager.jobs) == 1
    assert gateway.calls == [DEVICE_ID]
    asyncio.run(service.stop())


@pytest.mark.parametrize(
    "reason",
    [
        "LICENSE_REVOKED",
        "LICENSE_EXPIRED",
        "DEVICE_REVOKED",
        "DEVICE_NOT_ACTIVATED",
    ],
)
def test_inactive_entitlement_never_creates_background_job(
    tmp_path,
    monkeypatch,
    reason,
):
    service, manager, gateway, status = asyncio.run(
        _scan_once_with_new_item(
            tmp_path,
            monkeypatch,
            {"decision": "INACTIVE", "reason": reason},
        )
    )
    assert manager.jobs == []
    assert gateway.calls == [DEVICE_ID]
    assert status.last_error == reason
    asyncio.run(service.stop())


def test_unknown_entitlement_fails_closed_without_disabling_automation(
    tmp_path,
    monkeypatch,
):
    service, manager, gateway, status = asyncio.run(
        _scan_once_with_new_item(
            tmp_path,
            monkeypatch,
            {
                "decision": "UNKNOWN",
                "reason": "LICENSE_SERVICE_UNAVAILABLE",
            },
        )
    )
    assert manager.jobs == []
    assert status.last_error == "UNKNOWN"
    assert service._policies["user:7"]["auto_enqueue"] is True
    assert gateway.calls == [DEVICE_ID]
    asyncio.run(service.stop())


def test_legacy_automation_requires_background_license_context(tmp_path, monkeypatch):
    service, manager, gateway, status = asyncio.run(
        _scan_once_with_new_item(
            tmp_path,
            monkeypatch,
            {"decision": "ACTIVE", "reason": "ACTIVE"},
            policy_fields={"license_device_id": None},
        )
    )
    assert status.license_context_status == "REAUTH_REQUIRED"
    assert status.last_error == "BACKGROUND_LICENSE_CONTEXT_REQUIRED"
    assert manager.jobs == []
    assert gateway.calls == []
    asyncio.run(service.stop())


@pytest.mark.parametrize("field", ["vip_expires_at", "card_code"])
def test_legacy_vip_or_cardkey_cannot_replace_device_binding(
    tmp_path,
    monkeypatch,
    field,
):
    service, manager, _gateway, status = asyncio.run(
        _scan_once_with_new_item(
            tmp_path,
            monkeypatch,
            {"decision": "ACTIVE", "reason": "ACTIVE"},
            policy_fields={"license_device_id": None, field: "legacy-value"},
        )
    )
    assert status.license_context_status == "REAUTH_REQUIRED"
    assert manager.jobs == []
    asyncio.run(service.stop())


def test_entitlement_denial_does_not_consume_quota(tmp_path, monkeypatch):
    import app.db as db_module
    import app.quota as quota_module

    events: list[str] = []

    class _DB:
        def query(self, *_args):
            return self

        def filter(self, *_args):
            return self

        def first(self):
            return SimpleNamespace(is_active=True)

        def close(self):
            pass

    monkeypatch.setattr(db_module, "SessionLocal", lambda: _DB())
    monkeypatch.setattr(quota_module, "check_job_quota", lambda *_args: events.append("check"))
    monkeypatch.setattr(quota_module, "increment_job_quota", lambda *_args: events.append("increment"))
    service, manager, _gateway, _status = asyncio.run(
        _scan_once_with_new_item(
            tmp_path,
            monkeypatch,
            {"decision": "INACTIVE", "reason": "LICENSE_REVOKED"},
            identity=Identity(kind="user", user_id=7),
        )
    )
    assert manager.jobs == []
    assert events == []
    asyncio.run(service.stop())


def test_active_background_order_is_entitlement_quota_job_then_increment(
    tmp_path,
    monkeypatch,
):
    import app.db as db_module
    import app.quota as quota_module
    import app.automation.hongguo_monitor as monitor_module

    events: list[str] = []

    class _DB:
        def query(self, *_args):
            return self

        def filter(self, *_args):
            return self

        def first(self):
            return SimpleNamespace(is_active=True)

        def close(self):
            pass

    monkeypatch.setattr(db_module, "SessionLocal", lambda: _DB())
    monkeypatch.setattr(quota_module, "check_job_quota", lambda *_args: events.append("check"))
    monkeypatch.setattr(quota_module, "increment_job_quota", lambda *_args: events.append("increment"))

    settings = Settings(data_dir=tmp_path, max_queued_jobs=10)
    manager = _Manager(events)
    gateway = _Gateway({"decision": "ACTIVE", "reason": "ACTIVE"})
    platform = _Platform()
    monkeypatch.setattr(monitor_module, "get_platform", lambda _name: platform)
    service = HongguoMonitorService(settings, manager, gateway)
    identity = Identity(kind="user", user_id=7)
    asyncio.run(
        service.configure(
            identity,
            HongguoMonitorConfig(auto_enqueue=True),
            verified_device_id=DEVICE_ID,
        )
    )
    asyncio.run(service.scan_now(identity))
    platform.rows.append(DiscoverItem(id="new", title="new", platform=PlatformName.hongguo))
    asyncio.run(service.scan_now(identity))
    assert events == ["check", "job", "increment"]
    asyncio.run(service.stop())


def _request_headers(device_id: str):
    return {
        "X-Device-Id": device_id,
        "X-Device-Key-Algorithm": "ED25519",
        "X-Device-Proof-Timestamp": "1760000000",
        "X-Device-Proof-Nonce": "test-proof-nonce-123456",
        "X-Device-Proof-Signature": "test-proof-signature",
        "X-API-Key": "ops-test-key",
    }


def test_http_automation_saves_only_verified_device_id(tmp_path, monkeypatch):
    import app.automation.hongguo_monitor as monitor_module

    settings = get_settings()
    original_data_dir = settings.data_dir
    original_service = monitor_module._service
    monitor_module._service = None
    settings.data_dir = tmp_path
    app.dependency_overrides[require_identity] = lambda: Identity(
        kind="user", user_id=42, username="t13"
    )
    try:
        with TestClient(app) as client:
            response = client.put(
                "/v1/automation/hongguo-new",
                headers={key: value for key, value in _request_headers(DEVICE_ID).items() if key != "X-API-Key"},
                json={"auto_enqueue": True, "enabled": False},
            )
        assert response.status_code == 200
        payload = json.loads(
            (tmp_path / "automation" / "hongguo_monitors.json").read_text(
                encoding="utf-8"
            )
        )
        assert next(iter(payload.values()))["license_device_id"] == DEVICE_ID
        assert response.json()["license_context_status"] == "READY"
    finally:
        app.dependency_overrides.pop(require_identity, None)
        monitor_module._service = original_service
        settings.data_dir = original_data_dir


def test_http_automation_body_device_id_is_not_trusted(tmp_path, monkeypatch):
    import app.automation.hongguo_monitor as monitor_module

    settings = get_settings()
    original_data_dir = settings.data_dir
    original_service = monitor_module._service
    monitor_module._service = None
    settings.data_dir = tmp_path
    app.dependency_overrides[require_identity] = lambda: Identity(
        kind="user", user_id=43, username="t13"
    )
    try:
        with TestClient(app) as client:
            response = client.put(
                "/v1/automation/hongguo-new",
                headers=_request_headers(DEVICE_ID),
                json={
                    "auto_enqueue": True,
                    "device_id": "dev_" + "b" * 64,
                },
            )
        assert response.status_code == 422
        assert not (tmp_path / "automation" / "hongguo_monitors.json").exists()
    finally:
        app.dependency_overrides.pop(require_identity, None)
        monitor_module._service = original_service
        settings.data_dir = original_data_dir


def test_api_key_cannot_create_background_license_context(tmp_path, monkeypatch):
    import app.automation.hongguo_monitor as monitor_module

    settings = get_settings()
    original_data_dir = settings.data_dir
    original_service = monitor_module._service
    monitor_module._service = None
    settings.data_dir = tmp_path
    app.dependency_overrides[require_identity] = lambda: Identity(
        kind="api_key", is_ops=True
    )
    try:
        with TestClient(app) as client:
            response = client.put(
                "/v1/automation/hongguo-new",
                headers=_request_headers(DEVICE_ID),
                json={"auto_enqueue": True},
            )
        assert response.status_code == 403
        assert response.json()["detail"] == "BACKGROUND_LICENSE_CONTEXT_REQUIRED"
        assert not (tmp_path / "automation" / "hongguo_monitors.json").exists()
    finally:
        app.dependency_overrides.pop(require_identity, None)
        monitor_module._service = original_service
        settings.data_dir = original_data_dir
