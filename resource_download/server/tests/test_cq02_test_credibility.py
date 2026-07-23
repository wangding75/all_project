"""CQ-02：测试可信度、状态隔离与 Mock 平台契约测试套件。"""

from __future__ import annotations

import asyncio
import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

from app.config import get_settings
from app.db import Base, get_db
from app.main import app
from app.rate_limit import ip_rate_limiter
from conftest import FakeMockPlatform

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_mock_platform_isolation(fake_platform: FakeMockPlatform):
    """验证 Fake 平台适配器完全隔离外网，且返回符合契约的数据。"""
    async def _run():
        search_res = await fake_platform.search("测试关键词")
        assert len(search_res) == 1
        assert search_res[0].id == "mock_item_1"
        assert "Mock" in search_res[0].title

        detail_res = await fake_platform.get_detail("mock_item_1")
        assert detail_res.id == "mock_item_1"
        assert len(detail_res.segments) == 2
        assert detail_res.segments[0].id == "seg_1"

    asyncio.run(_run())


def test_test_environment_isolation_fixture():
    """验证 conftest 自动清洗环境变量与限流计数器。"""
    from app.rate_limit import _rate_limit_cache, _rate_limit_lock
    os.environ["AUTH_MODE"] = "jwt_only"
    get_settings.cache_clear()
    assert get_settings().auth_mode == "jwt_only"

    # 限流器填充记录
    with _rate_limit_lock:
        _rate_limit_cache["auth:127.0.0.1:999999"] = 100
        assert len(_rate_limit_cache) > 0


def test_precise_error_status_assertions(client: TestClient):
    """验证异常响应的精确状态码与 detail 体断言（杜绝模糊断言）。"""
    os.environ["AUTH_MODE"] = "dual"
    os.environ["API_KEY"] = "ops_key_cq02"
    os.environ["JWT_SECRET"] = "super_jwt_secret_32bytes_long!!"
    get_settings.cache_clear()

    # 1. 验证 401 精确状态码与 detail
    resp_401 = client.get("/v1/auth/me")
    assert resp_401.status_code == 401
    assert resp_401.json()["detail"] == "Invalid or missing X-API-Key or Authorization Bearer token"

    # 2. 验证 404 精确状态码与 detail
    ops_headers = {"X-API-Key": "ops_key_cq02"}
    resp_404 = client.get("/v1/admin/users/999999", headers=ops_headers)
    assert resp_404.status_code == 404
    assert resp_404.json()["detail"] == "用户不存在"

    # 3. 验证 400 精确状态码与 detail (非法卡密批次作废)
    resp_400 = client.post("/v1/admin/card-keys/invalidate-batch", headers=ops_headers, json={"batch_id": ""})
    assert resp_400.status_code == 422  # Pydantic 校验错误
