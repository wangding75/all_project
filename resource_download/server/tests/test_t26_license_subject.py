"""T26 license-subject quota, owner isolation, and SDK pin checks."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth import Identity
from app.db import Base
from app.idempotency import IdempotencyConflict, IdempotencyStore, request_fingerprint
from app.jobs.manager import JobManager, JobRecord
from app.models import PlatformName
from app.models_orm import LicenseUsageDaily
from app.quota import check_job_quota, increment_job_quota


def _identity(license_id: str = "lic_t26", device_id: str = "dev_a") -> Identity:
    return Identity(
        kind="user",
        user_id=7,
        license_id=license_id,
        device_id=device_id,
        plan_code="pro",
        plan_version=1,
        entitlement_schema_version=1,
        entitlements={"quota.daily_jobs": 2, "job.max_concurrency": 3},
        license_context_source="remote",
    )


@pytest.fixture
def quota_db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_license_usage_is_shared_across_devices(quota_db):
    first = _identity(device_id="dev_a")
    second = _identity(device_id="dev_b")

    check_job_quota(first, quota_db)
    increment_job_quota(first, quota_db)
    check_job_quota(second, quota_db)
    increment_job_quota(second, quota_db)

    with pytest.raises(HTTPException) as exc_info:
        check_job_quota(first, quota_db)
    assert exc_info.value.status_code == 429
    usage = quota_db.query(LicenseUsageDaily).one()
    assert usage.license_id == "lic_t26"
    assert usage.used_count == 2
    assert usage.limit_snapshot == 2


def test_malformed_entitlement_fails_closed(quota_db):
    identity = _identity()
    identity.entitlements = {"quota.daily_jobs": "untrusted"}
    with pytest.raises(HTTPException) as exc_info:
        check_job_quota(identity, quota_db)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "PLAN_ENTITLEMENT_INVALID"


def test_job_owner_requires_license_and_device_pair(tmp_path):
    from app.config import get_settings

    settings = get_settings().model_copy(update={"data_dir": tmp_path})
    manager = JobManager(settings)
    record = JobRecord(
        job_id="t26job",
        platform=PlatformName.fanqie,
        item_id="item",
        range_spec="all",
        options={},
        owner_kind="license_device",
        license_id="lic_t26",
        device_id="dev_a",
    )
    assert manager.can_access_job(record, _identity(device_id="dev_a"))
    assert not manager.can_access_job(record, _identity(device_id="dev_b"))
    assert not manager.can_access_job(record, _identity(license_id="lic_other", device_id="dev_a"))


def test_idempotency_scope_is_license_and_device_specific():
    store = IdempotencyStore()
    body = {"platform": "fanqie", "id": "same"}
    fingerprint = request_fingerprint(body)
    first = store.begin("license:lic_t26:device:dev_a", "k", fingerprint)
    assert first[0] is True
    store.complete("license:lic_t26:device:dev_a", "k", first[1], {"job_id": "one"})
    assert store.begin("license:lic_t26:device:dev_a", "k", fingerprint)[0] is False
    with pytest.raises(IdempotencyConflict):
        store.begin("license:lic_t26:device:dev_a", "k", request_fingerprint({"id": "other"}))
    assert store.begin("license:lic_t26:device:dev_b", "k", fingerprint)[0] is True


def test_rc4_vendor_pin_is_fixed():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "license_service_client-1.0.0rc4-py3-none-any.whl" in text
    assert "62E502DC2BAB6F925DACB4A51E92D4D39F9CD459E7C209C618C8FB46CC5C29C9" in text
