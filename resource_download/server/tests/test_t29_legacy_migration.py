"""T29 durable migration and legacy User/JWT isolation coverage."""

from __future__ import annotations

import asyncio
import json

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.auth import Identity
from app.config import get_settings
from app.idempotency import IdempotencyStore
from app.jobs import JobManager
from app.models import PlatformName
from app.models_orm import Base, IdempotencyRecord, LicenseUsageDaily
from app.main import app


def test_fresh_schema_and_repeat_migration_have_durable_subject_tables():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    names = set(inspect(engine).get_table_names())
    assert "license_usage_daily" in names
    assert "idempotency_records" in names
    assert IdempotencyRecord.__tablename__ == "idempotency_records"
    assert LicenseUsageDaily.__tablename__ == "license_usage_daily"


def test_idempotency_replay_survives_store_restart():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()
    first = IdempotencyStore()
    leader, entry = first.begin("license:lic-a:device:dev-a", "same-key", "fp-a", db=db)
    assert leader
    first.complete(
        "license:lic-a:device:dev-a",
        "same-key",
        entry,
        {"job_id": "job-a"},
        db=db,
    )
    second = IdempotencyStore()
    leader, replay = second.begin("license:lic-a:device:dev-a", "same-key", "fp-a", db=db)
    assert not leader
    assert second.wait(replay) == {"job_id": "job-a"}
    db.close()


def test_legacy_jobs_are_marked_unowned_and_never_reowned(tmp_path):
    async def run() -> None:
        settings = get_settings().model_copy(update={"data_dir": tmp_path})
        settings.jobs_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "job_id": "legacy-job",
            "platform": "hongguo",
            "item_id": "item-legacy",
            "status": "success",
            "files": [{"file_id": "legacy-file", "name": "legacy.mp4"}],
        }
        path = settings.jobs_dir / "legacy-job.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        manager = JobManager(settings=settings)
        await manager.load_jobs()
        record = await manager.get_job("legacy-job")
        assert record is not None
        assert record.legacy_unowned is True
        assert record.owner_kind == "legacy_unowned"
        assert record.license_id is None
        assert record.device_id is None
        assert record.files[0].legacy_unowned is True
        assert not manager.can_access_job(
            record,
            Identity(kind="license", license_id="lic-new", device_id="dev-new"),
        )
        persisted = json.loads(path.read_text(encoding="utf-8"))
        assert persisted["persistence_version"] == 2
        assert persisted["legacy_unowned"] is True
        assert persisted["files"][0]["owner_kind"] == "legacy_unowned"
        await manager.shutdown()

    asyncio.run(run())


def test_complete_license_subject_is_preserved_during_restart(tmp_path):
    async def run() -> None:
        settings = get_settings().model_copy(update={"data_dir": tmp_path})
        settings.jobs_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "job_id": "licensed-job",
            "platform": PlatformName.hongguo.value,
            "item_id": "item-licensed",
            "status": "success",
            "owner_kind": "license_device",
            "license_id": "lic-a",
            "device_id": "dev-a",
            "files": [{"file_id": "licensed-file", "name": "licensed.mp4"}],
        }
        path = settings.jobs_dir / "licensed-job.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        manager = JobManager(settings=settings)
        await manager.load_jobs()
        record = await manager.get_job("licensed-job")
        assert record is not None
        assert record.legacy_unowned is False
        assert record.files[0].license_id == "lic-a"
        assert record.files[0].device_id == "dev-a"
        await manager.shutdown()

    asyncio.run(run())


def test_legacy_user_auth_is_disabled_without_explicit_flag(monkeypatch):
    monkeypatch.delenv("LEGACY_USER_AUTH_ENABLED", raising=False)
    monkeypatch.setenv("JWT_SECRET", "t29-legacy-isolation-secret-32-bytes-long")
    get_settings.cache_clear()
    with TestClient(app) as client:
        response = client.post(
            "/v1/auth/register",
            json={"username": "legacy-disabled", "password": "password-123"},
        )
    assert response.status_code == 410
    assert response.json()["detail"] == "LEGACY_USER_AUTH_DISABLED"
    get_settings.cache_clear()
