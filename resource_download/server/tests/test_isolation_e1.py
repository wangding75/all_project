"""E1 多用户 Job & 文件隔离测试 (IDOR 防御)。"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import Base, get_db
from app.config import get_settings
from app.models_orm import User
from app.jobs import get_job_manager, JobRecord
from app.models import JobStatus, PlatformName, JobFile

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="db_session")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="client")
def fixture_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        c.headers.update(
            {
                "X-Device-Id": "dev_" + "1" * 64,
                "X-Device-Key-Algorithm": "ED25519",
                "X-Device-Proof-Timestamp": "1760000000",
                "X-Device-Proof-Nonce": "isolation-proof-nonce-123456",
                "X-Device-Proof-Signature": "isolation-proof-signature",
            }
        )
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_settings_and_jobs(tmp_path):
    settings = get_settings()
    original_auth_mode = settings.auth_mode
    original_api_key = settings.api_key
    original_data_dir = settings.data_dir

    settings.data_dir = tmp_path
    manager = get_job_manager()
    manager.settings = settings
    manager.settings.jobs_dir.mkdir(parents=True, exist_ok=True)
    manager.settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    manager._jobs.clear()

    from app.rate_limit import _rate_limit_cache
    _rate_limit_cache.clear()

    yield

    settings.auth_mode = original_auth_mode
    settings.api_key = original_api_key
    settings.data_dir = original_data_dir
    manager.settings = get_settings()
    manager._jobs.clear()
    _rate_limit_cache.clear()


def create_vip_user(client: TestClient, db, username: str, password: str = "password123") -> str:
    res = client.post("/v1/auth/register", json={"username": username, "password": password})
    assert res.status_code == 201
    user_id = res.json()["id"]

    user = db.query(User).filter(User.id == user_id).first()
    user.vip_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30)
    db.commit()

    login_res = client.post("/v1/auth/login", json={"username": username, "password": password})
    assert login_res.status_code == 200
    return login_res.json()["access_token"]


def test_user_job_isolation(client: TestClient, db_session, device_headers):
    """用户 A 创建的 Job，用户 B token 获取或取消均报 404 (IDOR 防御)。"""
    settings = get_settings()
    settings.auth_mode = "dual"

    token_a = create_vip_user(client, db_session, "user_a")
    token_b = create_vip_user(client, db_session, "user_b")

    # A 创建任务
    create_res = client.post(
        "/v1/jobs",
        json={"platform": "hongguo", "id": "12345", "range": "1-1"},
        headers={"Authorization": f"Bearer {token_a}", **device_headers},
    )
    assert create_res.status_code == 200
    job_id_a = create_res.json()["job_id"]

    # A 访问自己的 Job 正常 200
    get_a = client.get(f"/v1/jobs/{job_id_a}", headers={"Authorization": f"Bearer {token_a}"})
    assert get_a.status_code == 200
    assert get_a.json()["job_id"] == job_id_a

    # B 试图访问 A 的 Job 报 404
    get_b = client.get(f"/v1/jobs/{job_id_a}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_b.status_code == 404

    # B 试图取消 A 的 Job 报 404
    cancel_b = client.delete(f"/v1/jobs/{job_id_a}", headers={"Authorization": f"Bearer {token_b}"})
    assert cancel_b.status_code == 404


def test_user_list_and_summary_isolation(client: TestClient, db_session, device_headers):
    """列表与 summary 对用户 B 不暴露 A 的任务。"""
    settings = get_settings()
    settings.auth_mode = "dual"

    token_a = create_vip_user(client, db_session, "user_a_sum")
    token_b = create_vip_user(client, db_session, "user_b_sum")

    # A 创建 Job
    client.post(
        "/v1/jobs",
        json={"platform": "hongguo", "id": "66666", "range": "1-1"},
        headers={"Authorization": f"Bearer {token_a}", **device_headers},
    )

    # A 列出 Job
    list_a = client.get("/v1/jobs", headers={"Authorization": f"Bearer {token_a}"})
    assert list_a.status_code == 200
    assert list_a.json()["total"] == 1

    # B 列出 Job (应为 0)
    list_b = client.get("/v1/jobs", headers={"Authorization": f"Bearer {token_b}"})
    assert list_b.status_code == 200
    assert list_b.json()["total"] == 0
    assert len(list_b.json()["items"]) == 0

    # Summary 统计隔离
    sum_b = client.get("/v1/jobs/summary", headers={"Authorization": f"Bearer {token_b}"})
    assert sum_b.status_code == 200
    assert sum_b.json()["active_jobs"] == 0


def test_file_isolation_idor(client: TestClient, db_session):
    """用户 B 无法列出、下载或 open 用户 A Job 产出的文件。"""
    settings = get_settings()
    settings.auth_mode = "dual"

    token_a = create_vip_user(client, db_session, "user_file_a")
    token_b = create_vip_user(client, db_session, "user_file_b")

    # 手动放置 A 的产物文件
    manager = get_job_manager()
    job_id_a = "job_file_123"
    out_dir = settings.outputs_dir / job_id_a
    out_dir.mkdir(parents=True, exist_ok=True)
    file_path = out_dir / "episode1.mp4"
    file_path.write_bytes(b"dummy video data")

    rel_file_id = f"{job_id_a}/episode1.mp4"
    record_a = JobRecord(
        job_id=job_id_a,
        platform=PlatformName.hongguo,
        item_id="12345",
        range_spec="1-1",
        options={},
        status=JobStatus.success,
        files=[
            JobFile(
                file_id=rel_file_id,
                name="episode1.mp4",
                size=16,
                path=str(file_path),
            )
        ],
        owner_user_id=1,  # user_file_a's id
        owner_kind="user",
    )
    manager._jobs[job_id_a] = record_a

    # A 列文件 -> 可见
    files_a = client.get("/v1/files", headers={"Authorization": f"Bearer {token_a}"})
    assert files_a.status_code == 200
    assert len(files_a.json()["items"]) == 1
    assert files_a.json()["items"][0]["file_id"] == rel_file_id

    # B 列文件 -> 不可见
    files_b = client.get("/v1/files", headers={"Authorization": f"Bearer {token_b}"})
    assert files_b.status_code == 200
    assert len(files_b.json()["items"]) == 0

    # B 下载 A 的文件 -> 404
    dl_b = client.get(f"/v1/files/{rel_file_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert dl_b.status_code == 404

    # B open A 的文件 -> 404
    open_b = client.post(
        f"/v1/files/{rel_file_id}/open",
        json={"action": "play"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert open_b.status_code == 404

    # A 下载自己的文件 -> 200
    dl_a = client.get(f"/v1/files/{rel_file_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert dl_a.status_code == 200
    assert dl_a.content == b"dummy video data"


def test_ops_key_sees_all_in_dual_mode(client: TestClient, db_session, device_headers):
    """ops API Key 在 dual 模式下可以查看/下载全量任务与文件。"""
    settings = get_settings()
    settings.auth_mode = "dual"

    token_a = create_vip_user(client, db_session, "user_ops_a")
    create_res = client.post(
        "/v1/jobs",
        json={"platform": "hongguo", "id": "99999", "range": "1-1"},
        headers={"Authorization": f"Bearer {token_a}", **device_headers},
    )
    job_id_a = create_res.json()["job_id"]

    ops_headers = {"X-API-Key": settings.api_key}

    # ops 可以 GET A 的 Job
    get_ops = client.get(f"/v1/jobs/{job_id_a}", headers=ops_headers)
    assert get_ops.status_code == 200

    # ops 可以 list Jobs
    list_ops = client.get("/v1/jobs", headers=ops_headers)
    assert list_ops.status_code == 200
    assert list_ops.json()["total"] == 1


def test_dev_mode_key_behaves_as_ops(client: TestClient):
    """dev 模式使用 X-API-Key 行为与 ops 一致。"""
    settings = get_settings()
    settings.auth_mode = "dev"

    manager = get_job_manager()
    job_id = "dev_job_001"
    manager._jobs[job_id] = JobRecord(
        job_id=job_id,
        platform=PlatformName.fanqie,
        item_id="777",
        range_spec="all",
        options={},
        owner_user_id=888,
        owner_kind="user",
    )

    ops_headers = {"X-API-Key": settings.api_key}
    res = client.get(f"/v1/jobs/{job_id}", headers=ops_headers)
    assert res.status_code == 200
    assert res.json()["job_id"] == job_id


def test_legacy_job_json_compatibility(client: TestClient, db_session):
    """旧 Job JSON（无 owner 字段）默认仅 ops 可见，普通 user 不可见。"""
    settings = get_settings()
    settings.auth_mode = "dual"

    token_b = create_vip_user(client, db_session, "user_legacy")

    manager = get_job_manager()
    legacy_job_id = "legacy_001"
    manager._jobs[legacy_job_id] = JobRecord(
        job_id=legacy_job_id,
        platform=PlatformName.fanqie,
        item_id="111",
        range_spec="all",
        options={},
        owner_user_id=None,
        owner_kind=None,
    )

    # user 获取 legacy job -> 404
    get_b = client.get(f"/v1/jobs/{legacy_job_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_b.status_code == 404

    # ops 获取 legacy job -> 200
    ops_headers = {"X-API-Key": settings.api_key}
    get_ops = client.get(f"/v1/jobs/{legacy_job_id}", headers=ops_headers)
    assert get_ops.status_code == 200
