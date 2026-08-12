from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.db import Base, get_db
from app.main import app
from app.models import PlatformName


@pytest.fixture
def commercial_client(license_gateway_for_tests):
    settings = get_settings()
    settings.auth_mode = "dev"
    settings.api_key = "commercial-test-key"
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            client.headers.update(
                {
                    "X-Device-Id": "dev_" + "1" * 64,
                    "X-Device-Key-Algorithm": "ED25519",
                    "X-Device-Proof-Timestamp": "1760000000",
                    "X-Device-Proof-Nonce": "t22-proof-nonce-123456",
                    "X-Device-Proof-Signature": "t22-proof-signature",
                }
            )
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_default_auth_mode_is_dual() -> None:
    assert get_settings().auth_mode == "dual"


def test_runtime_cookie_is_accepted_but_split_from_persistence() -> None:
    from app.options import split_job_options

    persisted, runtime = split_job_options(
        PlatformName.fanqie,
        {"title": "demo", "cookie": "session-secret"},
    )
    assert persisted == {"title": "demo"}
    assert runtime == {"cookie": "session-secret"}


def test_search_failure_has_explicit_status(commercial_client, monkeypatch) -> None:
    from app.api import router as router_module

    class _BrokenPlatform:
        async def search(self, _query, page=1):  # noqa: ARG002
            raise RuntimeError("RUNTIME_INCOMPATIBLE: pinned Frida runtime is required")

    monkeypatch.setattr(router_module, "get_platform", lambda _name: _BrokenPlatform())
    response = commercial_client.get(
        "/v1/search?platform=fanqie&q=%E7%89%B9%E5%B7%A5%E6%98%93%E5%86%B7",
        headers={"X-API-Key": "commercial-test-key"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["platform_status"]["fanqie"] == "RUNTIME_INCOMPATIBLE"
    assert "RUNTIME_INCOMPATIBLE" in payload["platform_errors"]["fanqie"]


def test_idempotency_store_concurrent_duplicate_is_one_record() -> None:
    from app.idempotency import IdempotencyStore, request_fingerprint

    store = IdempotencyStore(ttl_seconds=10)
    payload = request_fingerprint({"platform": "hongguo", "id": "series-t22-concurrent"})
    results: list[dict] = []
    lock = threading.Lock()

    def submit() -> None:
        leader, entry = store.begin("user:22", "t22-concurrent-1", payload)
        if leader:
            time.sleep(0.05)
            store.complete("user:22", "t22-concurrent-1", entry, {"job_id": "job-t22-concurrent"})
        cached = entry.response if leader else store.wait(entry)
        with lock:
            results.append(cached or {})

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _item: submit(), range(2)))
    assert results == [{"job_id": "job-t22-concurrent"}, {"job_id": "job-t22-concurrent"}]


def test_frida_preflight_reports_target_mismatch(monkeypatch) -> None:
    from platforms.hongguo import frida_compat

    monkeypatch.setattr(frida_compat, "_target_info", lambda: ("17.15.4", "x86_64", "emu"))
    with pytest.raises(frida_compat.FridaCompatibilityError) as exc_info:
        frida_compat.ensure_compatible()
    assert str(exc_info.value).startswith("RUNTIME_INCOMPATIBLE:")
    assert exc_info.value.details["target_frida_server"] == "17.15.4"
