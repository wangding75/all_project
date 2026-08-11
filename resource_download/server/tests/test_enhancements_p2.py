"""功能增强与防御性解析测试套件 (S-P2-1, S-P2-2, S-P2-9, U-P2-1)。"""

from __future__ import annotations

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch
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
from app.jobs.manager import JobManager, JobRecord, JobStatus, PlatformName
from app.main import app
from app.models import DetailResponse, SegmentInfo
from platforms.fanqie.web_ssr import extract_initial_state

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
        c.headers.update(
            {
                "X-Device-Id": "dev_" + "1" * 64,
                "X-Device-Key-Algorithm": "ED25519",
                "X-Device-Proof-Timestamp": "1760000000",
                "X-Device-Proof-Nonce": "p2-proof-nonce-123456",
                "X-Device-Proof-Signature": "p2-proof-signature",
            }
        )
        yield c
    app.dependency_overrides.clear()


def test_extract_initial_state_raw_decode():
    """测试 raw_decode 解析嵌套及复杂 JSON 字符串。"""
    html_sample = (
        '<html><body><script>'
        'window.__INITIAL_STATE__={"common":{"css":"body{font-family:\\"Arial\\";}"},"reader":{"title":"章{一}"}};'
        '</script></body></html>'
    )
    data = extract_initial_state(html_sample)
    assert "common" in data
    assert data["reader"]["title"] == "章{一}"


def test_job_manager_eviction(tmp_path):
    """测试 JobManager 内存淘汰机制 (S-P2-9)。"""
    async def _run_test():
        settings = get_settings()
        manager = JobManager(settings)

        # 填充 210 个已完成任务
        for i in range(210):
            record = JobRecord(
                job_id=f"job_{i:03d}",
                platform=PlatformName.hongguo,
                item_id="123",
                range_spec="all",
                options={},
                status=JobStatus.success,
                updated_at=f"2026-07-23T10:{i//60:02d}:{i%60:02d}Z",
            )
            manager._jobs[f"job_{i:03d}"] = record

        # 触发新任务创建与淘汰
        await manager.create_job(PlatformName.hongguo, "123", range_spec="all")

        # 验证内存中任务数量不超过 200 (包含新建的任务)
        assert len(manager._jobs) <= 200
        # 验证最旧的任务 job_000 已被淘汰
        assert "job_000" not in manager._jobs

    asyncio.run(_run_test())


def test_detail_pagination(client: TestClient):
    """测试 /v1/detail 选集列表的分页能力 (U-P2-1)。"""
    os.environ["AUTH_MODE"] = "dev"
    os.environ["API_KEY"] = "dev-key-change-me"
    get_settings.cache_clear()

    mock_detail = DetailResponse(
        platform=PlatformName.hongguo,
        id="test_id_100",
        title="测试剧集",
        segments=[
            SegmentInfo(id="seg_1", title="第 1 集", index=1),
            SegmentInfo(id="seg_2", title="第 2 集", index=2),
            SegmentInfo(id="seg_3", title="第 3 集", index=3),
            SegmentInfo(id="seg_4", title="第 4 集", index=4),
            SegmentInfo(id="seg_5", title="第 5 集", index=5),
        ],
    )

    mock_platform = AsyncMock()
    mock_platform.get_detail.return_value = mock_detail

    with patch("app.api.router.get_platform", return_value=mock_platform):
        headers = {"X-API-Key": "dev-key-change-me"}
        resp = client.get(
            "/v1/detail",
            params={"platform": "hongguo", "id": "test_id_100", "page": 1, "page_size": 2},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "segments" in data
        assert len(data["segments"]) == 2
        assert data["segments"][0]["id"] == "seg_1"
        assert data["segments"][1]["id"] == "seg_2"
        assert data["extra"]["page"] == 1
        assert data["extra"]["page_size"] == 2
        assert data["extra"]["total_segments"] == 5
