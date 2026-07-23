"""Stage E6 正式发行与 v1.0.0 上线门禁测试套件。"""

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

from app import __version__
from app.config import get_settings
from app.db import Base, get_db
from app.main import app

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


def test_version_consistency(client: TestClient):
    """测试版本号全链路对齐为 1.0.0。"""
    assert __version__ == "1.0.0"

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "1.0.0"


def test_release_gate_file_exists():
    """测试 release_gate.md 与 release.md 文档完整性。"""
    repo_root = Path(__file__).resolve().parents[2]
    gate_file = repo_root / "docs" / "release_gate.md"
    release_file = repo_root / "docs" / "release.md"

    assert gate_file.exists(), f"未查找到 release_gate.md 文件: {gate_file}"
    assert release_file.exists(), f"未查找到 release.md 文件: {release_file}"

    gate_content = gate_file.read_text(encoding="utf-8")
    assert "v1.0.0" in gate_content
    assert "Release Gate Passed" in gate_content
