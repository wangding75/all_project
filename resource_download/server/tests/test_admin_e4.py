"""Stage E4 管理与运维能力测试用例。"""

from __future__ import annotations

import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 确保导入路径包含 server 目录
server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

from app.config import get_settings
from app.db import Base, get_db
from app.main import app
from app.models_orm import CardKey, User

# 内存 SQLite 数据库与 StaticPool
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


def test_admin_permission_control(client: TestClient):
    """测试管理员接口鉴权控制：非 ops 身份返回 403，ops 返回 200。"""
    os.environ["AUTH_MODE"] = "dual"
    os.environ["API_KEY"] = "ops_secret_key_123"
    os.environ["JWT_SECRET"] = "super_jwt_secret_32bytes_long!!"
    get_settings.cache_clear()

    # 1. 注册普通用户
    reg_resp = client.post("/v1/auth/register", json={"username": "user1", "password": "password123"})
    assert reg_resp.status_code == 201
    user_id = reg_resp.json()["id"]

    # 登录获取普通用户 token
    login_resp = client.post("/v1/auth/login", json={"username": "user1", "password": "password123"})
    token = login_resp.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {token}"}

    # 2. 普通用户请求管理员接口 -> 应被拒 403 Forbidden
    resp = client.get(f"/v1/admin/users/{user_id}", headers=user_headers)
    assert resp.status_code == 403

    # 3. 使用 ops API Key 请求管理员接口 -> 成功 200 OK
    ops_headers = {"X-API-Key": "ops_secret_key_123"}
    resp = client.get(f"/v1/admin/users/{user_id}", headers=ops_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == user_id
    assert data["username"] == "user1"
    assert data["is_active"] is True


def test_ban_unban_user_flow(client: TestClient):
    """测试封禁/解封用户及 token 即时熔断机制。"""
    os.environ["AUTH_MODE"] = "dual"
    os.environ["API_KEY"] = "ops_key_abc"
    os.environ["JWT_SECRET"] = "super_jwt_secret_32bytes_long!!"
    get_settings.cache_clear()

    ops_headers = {"X-API-Key": "ops_key_abc"}

    # 注册并登录用户
    client.post("/v1/auth/register", json={"username": "target_user", "password": "password123"})
    login_resp = client.post("/v1/auth/login", json={"username": "target_user", "password": "password123"})
    token = login_resp.json()["access_token"]
    user_id = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["id"]

    user_headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/v1/auth/me", headers=user_headers).status_code == 200

    # ops 封禁该用户
    ban_resp = client.post(
        f"/v1/admin/users/{user_id}/status",
        headers=ops_headers,
        json={"is_active": False},
    )
    assert ban_resp.status_code == 200
    assert ban_resp.json()["is_active"] is False

    # 被封禁后，用户旧 token 发起 API 请求应抛出 401
    assert client.get("/v1/auth/me", headers=user_headers).status_code == 401

    # 被封禁后，重新登录也应抛出 401
    login_retry = client.post("/v1/auth/login", json={"username": "target_user", "password": "password123"})
    assert login_retry.status_code == 401

    # ops 解封该用户
    unban_resp = client.post(
        f"/v1/admin/users/{user_id}/status",
        headers=ops_headers,
        json={"is_active": True},
    )
    assert unban_resp.status_code == 200
    assert unban_resp.json()["is_active"] is True

    # 解封后恢复访问
    assert client.get("/v1/auth/me", headers=user_headers).status_code == 200


def test_invalidate_card_key_batch(client: TestClient, db_session):
    """测试按批次作废卡密及用户卡密核销拦截。"""
    os.environ["AUTH_MODE"] = "dual"
    os.environ["API_KEY"] = "ops_key_abc"
    os.environ["JWT_SECRET"] = "super_jwt_secret_32bytes_long!!"
    get_settings.cache_clear()

    ops_headers = {"X-API-Key": "ops_key_abc"}

    # 手动在 DB 中植入同一批次的卡密
    c1 = CardKey(code="CARD-BATCH1-01", duration_days=30, batch_id="B_BAD_2026")
    c2 = CardKey(code="CARD-BATCH1-02", duration_days=30, batch_id="B_BAD_2026")
    c3 = CardKey(code="CARD-GOOD-01", duration_days=30, batch_id="B_GOOD_2026")
    db_session.add_all([c1, c2, c3])
    db_session.commit()

    # 普通用户注册登录
    client.post("/v1/auth/register", json={"username": "test_redeemer", "password": "password123"})
    token = client.post("/v1/auth/login", json={"username": "test_redeemer", "password": "password123"}).json()["access_token"]
    user_headers = {"Authorization": f"Bearer {token}"}

    # 作废批次 B_BAD_2026
    inv_resp = client.post(
        "/v1/admin/card-keys/invalidate-batch",
        headers=ops_headers,
        json={"batch_id": "B_BAD_2026"},
    )
    assert inv_resp.status_code == 200
    assert inv_resp.json()["invalidated_count"] == 2

    # Redeem 已经是 License Service activation proxy；本地 CardKey 作废只
    # 影响历史 RD 表，不得阻断或完成新的 Device License 激活。
    activation = {
        "device_id": "dev_" + "1" * 64,
        "device_key_algorithm": "ED25519",
        "device_public_key": "dGVzdC1wdWJsaWMta2V5",
        "proof": {
            "timestamp": 1760000000,
            "nonce": "activation-proof-nonce-1234",
            "signature": "activation-proof-signature",
        },
    }
    r1 = client.post(
        "/v1/auth/redeem",
        headers=user_headers,
        json={"card_code": "CARD-BATCH1-01", **activation},
    )
    assert r1.status_code == 200
    r3 = client.post(
        "/v1/auth/redeem",
        headers=user_headers,
        json={"card_code": "CARD-GOOD-01", **activation},
    )
    assert r3.status_code == 200
    assert r3.json()["success"] is True
    db_session.expire_all()
    assert db_session.query(CardKey).filter(CardKey.code == "CARD-GOOD-01").one().is_used is False


def test_admin_list_users(client: TestClient, db_session):
    """测试管理员列表与明细查询。"""
    os.environ["AUTH_MODE"] = "dual"
    os.environ["API_KEY"] = "ops_key_abc"
    os.environ["JWT_SECRET"] = "super_jwt_secret_32bytes_long!!"
    get_settings.cache_clear()

    ops_headers = {"X-API-Key": "ops_key_abc"}

    r1 = client.post("/v1/auth/register", json={"username": "user_01", "password": "password123"})
    assert r1.status_code == 201, f"user_01 register failed: {r1.text}"
    r2 = client.post("/v1/auth/register", json={"username": "user_02", "password": "password123"})
    assert r2.status_code == 201, f"user_02 register failed: {r2.text}"

    list_resp = client.get("/v1/admin/users", headers=ops_headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 2
    assert len(data["users"]) == 2
    usernames = [u["username"] for u in data["users"]]
    assert "user_01" in usernames and "user_02" in usernames
