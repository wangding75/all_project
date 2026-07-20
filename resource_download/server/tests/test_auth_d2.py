"""卡密兑换与 VIP 门闸的集成测试。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import Base, get_db
from app.config import get_settings
from app.models_orm import CardKey

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
    """每次测试前后重置 settings 状态。"""
    settings = get_settings()
    original_auth_mode = settings.auth_mode
    original_api_key = settings.api_key
    yield
    settings.auth_mode = original_auth_mode
    settings.api_key = original_api_key


# --- 测试用例矩阵 ---

def test_redeem_no_auth(client):
    # 1. redeem 无凭证 -> 401
    resp = client.post("/v1/auth/redeem", json={"card_code": "RD-SOMECODE"})
    assert resp.status_code == 401


def test_redeem_api_key(client):
    # 2. redeem + X-API-Key -> 400 或 403，提示「请使用用户登录后兑换」
    get_settings().auth_mode = "dual"
    get_settings().api_key = "test-api-key"
    resp = client.post(
        "/v1/auth/redeem",
        json={"card_code": "RD-SOMECODE"},
        headers={"X-API-Key": "test-api-key"},
    )
    assert resp.status_code in (400, 403)
    assert "请使用用户登录后兑换" in resp.json()["detail"]


def test_redeem_success_and_duplicate(client, db_session):
    # 3. dual 用户 JWT + 未用卡 -> 200，vip_expires_at 在未来
    # 4. 同码再 redeem -> 400
    get_settings().auth_mode = "dual"

    # 在测试 DB 中生成一张未使用的卡密
    card = CardKey(code="RD-TESTCARD123", duration_days=30, is_used=False)
    db_session.add(card)
    db_session.commit()

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

    # 首次兑换 -> 成功 200
    resp = client.post(
        "/v1/auth/redeem",
        json={"card_code": "RD-TESTCARD123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["vip_expires_at"] != ""

    # 检查 /me 接口中用户的 vip_expires_at 已更新且非空
    me_resp = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["vip_expires_at"] is not None

    # 重复兑换同张卡 -> 400 Card already used
    resp2 = client.post(
        "/v1/auth/redeem",
        json={"card_code": "RD-TESTCARD123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 400
    assert "卡密已被使用" in resp2.json()["detail"]


def test_redeem_nonexistent_card(client):
    # 5. 不存在码 -> 400
    get_settings().auth_mode = "dual"

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

    resp = client.post(
        "/v1/auth/redeem",
        json={"card_code": "RD-NONEXISTENT"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "卡密不存在" in resp.json()["detail"]


def test_jobs_vip_gate(client, db_session):
    # 6. dual 非 VIP 用户 POST /v1/jobs 合法最小 body -> 403
    # 7. dual 先 redeem 成 VIP 再 POST /v1/jobs -> status != 403
    # 8. dual 或 dev + 合法 X-API-Key POST /v1/jobs -> status != 403
    get_settings().auth_mode = "dual"
    get_settings().api_key = "test-api-key"

    # 插入未使用卡密
    card = CardKey(code="RD-TESTCARD123", duration_days=30, is_used=False)
    db_session.add(card)
    db_session.commit()

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

    # 最小 jobs 请求参数
    jobs_body = {"platform": "fanqie", "id": "12345", "range": "1-1"}

    # 6. dual 非 VIP 用户创建任务 -> 403
    resp = client.post(
        "/v1/jobs",
        json=jobs_body,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert "需要 VIP，请兑换卡密" in resp.json()["detail"]

    # 7. 兑换卡密升级为 VIP
    redeem_resp = client.post(
        "/v1/auth/redeem",
        json={"card_code": "RD-TESTCARD123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert redeem_resp.status_code == 200

    # 再次创建任务 -> status != 403 (排除被 VIP 拦截，后端其它逻辑处理可能触发 502/429/400 等其它异常，但不是 403)
    resp2 = client.post(
        "/v1/jobs",
        json=jobs_body,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code != 403

    # 8. dual 模式下使用有效 X-API-Key 创建任务 -> 绕过 VIP 拦截， status != 403
    resp3 = client.post(
        "/v1/jobs",
        json=jobs_body,
        headers={"X-API-Key": "test-api-key"},
    )
    assert resp3.status_code != 403

    # dev 模式下使用有效 X-API-Key 创建任务 -> 绕过 VIP 拦截， status != 403
    get_settings().auth_mode = "dev"
    resp4 = client.post(
        "/v1/jobs",
        json=jobs_body,
        headers={"X-API-Key": "test-api-key"},
    )
    assert resp4.status_code != 403
