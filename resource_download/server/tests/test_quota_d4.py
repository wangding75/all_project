"""限流与每日配额的集成测试。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import Base, get_db
from app.config import get_settings

# 配置内存 SQLite 数据库用于测试
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="db_session")
def fixture_db_session():
    """每个测试前后创建和清理数据库表。"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="client")
def fixture_client(db_session):
    """FastAPI TestClient 夹具，覆盖 get_db 依赖。"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_settings():
    """每次测试前后重置 settings 状态和限流缓存。"""
    settings = get_settings()
    original_auth_mode = settings.auth_mode
    original_api_key = settings.api_key
    original_vip_jobs = settings.vip_jobs_per_day
    original_rate_limit = settings.rate_limit_per_minute
    original_rate_limit_auth = settings.rate_limit_auth_per_minute

    # 清空限流全局缓存以防测试干扰
    from app.rate_limit import _rate_limit_lock, _rate_limit_cache
    with _rate_limit_lock:
        _rate_limit_cache.clear()

    yield

    settings.auth_mode = original_auth_mode
    settings.api_key = original_api_key
    settings.vip_jobs_per_day = original_vip_jobs
    settings.rate_limit_per_minute = original_rate_limit
    settings.rate_limit_auth_per_minute = original_rate_limit_auth


# --- 测试用例 ---

def test_quota_limit_after_license_active(client, db_session, device_headers, monkeypatch):
    # License ACTIVE 后仍由 RD 自己执行每日配额。
    # 2. 同上第三次 jobs -> 429，文案含配额/用尽
    get_settings().auth_mode = "dual"
    get_settings().vip_jobs_per_day = 2

    class _QuotaPlatform:
        async def resolve_download(self, resource_id, **kwargs):
            return [{
                "download_mode": "direct",
                "resource_id": resource_id,
                "url": "https://cdn.example.invalid/file.mp4",
                "suggested_filename": "file.mp4",
            }]

    monkeypatch.setattr("app.api.router.get_platform", lambda _name: _QuotaPlatform())

    # 注册并登录用户
    client.post(
        "/v1/auth/register",
        json={"username": "user123", "password": "password123"},
    )
    login_resp = client.post(
        "/v1/auth/login",
        json={"username": "user123", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    jobs_body = {"platform": "fanqie", "resource_id": "12345", "range": "1-1"}
    headers = {"Authorization": f"Bearer {token}", **device_headers}

    # 第一次建任务 -> 成功
    resp1 = client.post(
        "/v1/resolve",
        json=jobs_body,
        headers=headers,
    )
    assert resp1.status_code not in (403, 429)

    # 第二次建任务 -> 成功
    resp2 = client.post(
        "/v1/resolve",
        json=jobs_body,
        headers=headers,
    )
    assert resp2.status_code not in (403, 429)

    # 第三次建任务 -> 429 今日下载配额已用尽
    resp3 = client.post(
        "/v1/resolve",
        json=jobs_body,
        headers=headers,
    )
    assert resp3.status_code == 429
    assert "今日下载配额已用尽" in resp3.json()["detail"]


def test_quota_bypass_for_ops(client, device_headers):
    # 3. VIP_JOBS_PER_DAY=1，多次 Key jobs -> 不因配额 429
    get_settings().auth_mode = "dual"
    get_settings().api_key = "test-api-key"
    get_settings().vip_jobs_per_day = 1

    jobs_body = {"platform": "fanqie", "resource_id": "12345", "range": "1-1"}

    # 使用 API Key 连续建 5 次任务 -> 应该全部通过，不计入/不拦截配额
    for _ in range(5):
        resp = client.post(
            "/v1/resolve",
            json=jobs_body,
        headers={"X-API-Key": "test-api-key", **device_headers},
        )
        assert resp.status_code != 429


def test_global_rate_limit(client):
    # 4. RATE_LIMIT_PER_MINUTE=3，/v1/version×4 -> 第 4 次 429
    get_settings().auth_mode = "dual"
    get_settings().api_key = "test-api-key"
    get_settings().rate_limit_per_minute = 3

    # 前 3 次请求 -> 成功
    for _ in range(3):
        resp = client.get("/v1/version", headers={"X-API-Key": "test-api-key"})
        assert resp.status_code != 429

    # 第 4 次请求 -> 429
    resp4 = client.get("/v1/version", headers={"X-API-Key": "test-api-key"})
    assert resp4.status_code == 429
    assert "请求过于频繁" in resp4.json()["detail"]


def test_auth_rate_limit(client):
    # 5. RATE_LIMIT_AUTH_PER_MINUTE=2，login×3 -> 第 3 次 429
    get_settings().auth_mode = "dual"
    get_settings().rate_limit_auth_per_minute = 2

    login_body = {"username": "user123", "password": "password123"}

    # 前 2 次调用 -> 成功
    for _ in range(2):
        resp = client.post("/v1/auth/login", json=login_body)
        assert resp.status_code != 429

    # 第 3 次调用 -> 429
    resp3 = client.post("/v1/auth/login", json=login_body)
    assert resp3.status_code == 429
    assert "请求过于频繁" in resp3.json()["detail"]


def test_health_not_rate_limited(client):
    # 6. 触发全站限流后仍 GET /health -> 200
    get_settings().auth_mode = "dual"
    get_settings().api_key = "test-api-key"
    get_settings().rate_limit_per_minute = 3

    # 对业务接口请求 3 次
    for _ in range(3):
        resp = client.get("/v1/version", headers={"X-API-Key": "test-api-key"})
        assert resp.status_code != 429

    # 第 4 次请求触发限流 429
    resp4 = client.get("/v1/version", headers={"X-API-Key": "test-api-key"})
    assert resp4.status_code == 429

    # 请求健康探活接口 -> 仍应该返回 200，说明 /health 被成功豁免了
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
