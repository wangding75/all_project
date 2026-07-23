"""用户认证系统的单元与集成测试。"""

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

    from app.rate_limit import _rate_limit_lock, _rate_limit_cache
    with _rate_limit_lock:
        _rate_limit_cache.clear()

    yield
    settings.auth_mode = original_auth_mode
    settings.api_key = original_api_key


# --- 测试用例矩阵 ---

def test_register_success(client):
    # 1. register -> 201，且无 password 字段
    resp = client.post(
        "/v1/auth/register",
        json={"username": "user123", "password": "password123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["username"] == "user123"
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate(client):
    # 2. 重复 username -> 400
    resp = client.post(
        "/v1/auth/register",
        json={"username": "user123", "password": "password123"},
    )
    assert resp.status_code == 201
    resp2 = client.post(
        "/v1/auth/register",
        json={"username": "user123", "password": "password456"},
    )
    assert resp2.status_code == 400
    assert "用户名已存在" in resp2.json()["detail"]


def test_register_invalid(client):
    # 3. 非法 username / 密码 < 8 / 密码过长 -> 400 或 422 (Pydantic)
    # 用户名过短
    resp = client.post(
        "/v1/auth/register",
        json={"username": "us", "password": "password123"},
    )
    assert resp.status_code in (400, 422)

    # 用户名含有非法字符
    resp = client.post(
        "/v1/auth/register",
        json={"username": "user-invalid", "password": "password123"},
    )
    assert resp.status_code in (400, 422)

    # 密码长度小于 8
    resp = client.post(
        "/v1/auth/register",
        json={"username": "user123", "password": "short"},
    )
    assert resp.status_code in (400, 422)

    # 密码过长 (超过 72 字节)
    resp = client.post(
        "/v1/auth/register",
        json={"username": "user123", "password": "a" * 73},
    )
    assert resp.status_code in (400, 422)


def test_login_success(client):
    # 4. login 正确 -> 200，含 access_token、token_type=bearer、expires_in
    # 注册用户
    client.post(
        "/v1/auth/register",
        json={"username": "user123", "password": "password123"},
    )

    # 登录
    resp = client.post(
        "/v1/auth/login",
        json={"username": "user123", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert "vip_expires_at" in data


def test_login_failures(client):
    # 5. login 错密 / 不存在用户 -> 401
    client.post(
        "/v1/auth/register",
        json={"username": "user123", "password": "password123"},
    )

    # 密码错误
    resp = client.post(
        "/v1/auth/login",
        json={"username": "user123", "password": "wrongpassword"},
    )
    assert resp.status_code == 401

    # 用户不存在
    resp = client.post(
        "/v1/auth/login",
        json={"username": "nouser", "password": "password123"},
    )
    assert resp.status_code == 401


def test_dual_bearer_me(client):
    # 6. dual + Bearer -> GET /v1/auth/me 200
    get_settings().auth_mode = "dual"

    client.post(
        "/v1/auth/register",
        json={"username": "user123", "password": "password123"},
    )
    login_resp = client.post(
        "/v1/auth/login",
        json={"username": "user123", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    resp = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "user123"


def test_dual_bad_token_me(client):
    # 7. dual + 坏 token -> me 401
    get_settings().auth_mode = "dual"
    resp = client.get(
        "/v1/auth/me",
        headers={"Authorization": "Bearer badtoken"},
    )
    assert resp.status_code == 401
    assert "Invalid or expired token" in resp.json()["detail"]


def test_dual_key_me_fails(client):
    # 8. dual + 合法 Key -> me 400/403（非用户）
    get_settings().auth_mode = "dual"
    get_settings().api_key = "test-api-key"

    resp = client.get(
        "/v1/auth/me",
        headers={"X-API-Key": "test-api-key"},
    )
    assert resp.status_code in (400, 403)
    assert "非用户身份" in resp.json()["detail"]


def test_dual_key_protected_route(client):
    # 9. dual + 合法 Key -> 受保护接口非 401
    get_settings().auth_mode = "dual"
    get_settings().api_key = "test-api-key"

    resp = client.get(
        "/v1/version",
        headers={"X-API-Key": "test-api-key"},
    )
    assert resp.status_code != 401


def test_dual_bearer_protected_route(client):
    # 10. dual + 合法 Bearer -> 受保护接口非 401
    get_settings().auth_mode = "dual"

    client.post(
        "/v1/auth/register",
        json={"username": "user123", "password": "password123"},
    )
    login_resp = client.post(
        "/v1/auth/login",
        json={"username": "user123", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    resp = client.get(
        "/v1/version",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code != 401


def test_dev_key_protected_route(client):
    # 11. dev + 合法 Key -> 受保护接口非 401
    get_settings().auth_mode = "dev"
    get_settings().api_key = "test-api-key"

    resp = client.get(
        "/v1/version",
        headers={"X-API-Key": "test-api-key"},
    )
    assert resp.status_code != 401


def test_dev_bearer_only_unauthorized(client):
    # 12. dev + 仅 Bearer（无 Key）-> 401（忽略 JWT）
    get_settings().auth_mode = "dev"

    client.post(
        "/v1/auth/register",
        json={"username": "user123", "password": "password123"},
    )
    login_resp = client.post(
        "/v1/auth/login",
        json={"username": "user123", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    resp = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401
