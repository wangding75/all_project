"""CQ-01：版本权威源、配置与单 Worker 运行约束测试套件。"""

from __future__ import annotations

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

from app import __version__
from app.config import get_settings
from app.db import Base, get_db
from app.main import app
from app.version import VERSION

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


def test_version_single_source_of_truth(client: TestClient):
    """验证版本权威源全链路一致性。"""
    # 1. 常量导出对齐
    assert VERSION == "1.0.0"
    assert __version__ == VERSION

    # 2. /health 端口版本对齐
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["version"] == VERSION

    # 3. /v1/version 端口真实版本与更新状态对齐
    ver_resp = client.get("/v1/version")
    assert ver_resp.status_code == 200
    v_data = ver_resp.json()
    assert v_data["version"] == VERSION
    assert v_data["latest_version"] == VERSION
    assert v_data["update_check_enabled"] is False
    assert v_data["has_update"] is False


def test_single_worker_enforcement():
    """验证 WORKERS > 1 时启动流程强行阻断抛错。"""
    os.environ["WORKERS"] = "2"
    get_settings.cache_clear()

    try:
        # 当以 WORKERS=2 运行测试客户端时，触发 lifespan 校验抛出 RuntimeError
        with pytest.raises(RuntimeError, match="仅支持单进程/单 Worker 模式运行"):
            with TestClient(app):
                pass
    finally:
        os.environ["WORKERS"] = "1"
        get_settings.cache_clear()
