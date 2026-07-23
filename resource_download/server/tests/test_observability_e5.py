"""Stage E5 可观测性与备份功能自动化测试套件。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
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
from app.logger import metrics_tracker
from app.main import app
from app.models_orm import User

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


def test_admin_health_endpoint(client: TestClient):
    """测试 /v1/admin/health 运维探活接口。"""
    os.environ["AUTH_MODE"] = "dual"
    os.environ["API_KEY"] = "ops_key_e5"
    os.environ["JWT_SECRET"] = "super_jwt_secret_32bytes_long!!"
    get_settings.cache_clear()

    ops_headers = {"X-API-Key": "ops_key_e5"}

    resp = client.get("/v1/admin/health", headers=ops_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db_status"] == "ok"
    assert "disk_free_human" in data
    assert "active_jobs" in data
    assert "sign_pool_summary" in data


def test_admin_metrics_endpoint(client: TestClient):
    """测试 /v1/admin/metrics 指标导出与计数刷新。"""
    os.environ["AUTH_MODE"] = "dual"
    os.environ["API_KEY"] = "ops_key_e5"
    os.environ["JWT_SECRET"] = "super_jwt_secret_32bytes_long!!"
    get_settings.cache_clear()

    ops_headers = {"X-API-Key": "ops_key_e5"}

    # 模拟指标更新
    metrics_tracker.inc_request()
    metrics_tracker.record_job_created("fanqie")
    metrics_tracker.record_job_success("fanqie")

    resp = client.get("/v1/admin/metrics", headers=ops_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_requests"] >= 1
    assert data["jobs_created_count"] >= 1
    assert data["jobs_success_count"] >= 1
    assert "fanqie" in data["platform_stats"]


def test_sqlite_online_backup_and_restore(tmp_path: Path):
    """测试 SQLite 在线热备份与还原逻辑。"""
    import sqlite3

    # 创建测试源数据库与目标备份路径
    src_db = tmp_path / "test_app.db"
    backup_db = tmp_path / "test_backup.db"
    restored_db = tmp_path / "test_restored.db"

    # 1. 写入测试数据
    conn = sqlite3.connect(str(src_db))
    conn.execute("CREATE TABLE dummy (id INT, val TEXT);")
    conn.execute("INSERT INTO dummy VALUES (1, 'hello_e5');")
    conn.commit()

    # 2. 执行在线备份
    target_conn = sqlite3.connect(str(backup_db))
    with target_conn:
        conn.backup(target_conn)
    target_conn.close()
    conn.close()

    assert backup_db.exists()
    assert backup_db.stat().st_size > 0

    # 3. 从备份还原到 restored_db
    b_conn = sqlite3.connect(str(backup_db))
    r_conn = sqlite3.connect(str(restored_db))
    with r_conn:
        b_conn.backup(r_conn)
    b_conn.close()

    # 4. 验证还原后的数据一致性
    cursor = r_conn.cursor()
    cursor.execute("SELECT val FROM dummy WHERE id = 1;")
    row = cursor.fetchone()
    r_conn.close()

    assert row is not None
    assert row[0] == "hello_e5"
