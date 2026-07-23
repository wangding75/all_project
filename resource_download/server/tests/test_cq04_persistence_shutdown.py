"""CQ-04：原子持久化、坏 JSON 隔离与正常退出恢复测试套件。"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable
import pytest

server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

from app.jobs import JobManager
from app.models import JobStatus, PlatformName
from app.config import Settings
from platforms.base import BasePlatform
from unittest.mock import patch
import platforms.registry as registry


class HangMockPlatform(BasePlatform):
    name = "mock_hang"

    async def search(self, query: str, page: int = 1, **kwargs: Any):
        return []

    async def get_detail(self, item_id: str, **kwargs: Any):
        raise NotImplementedError

    async def download(
        self,
        item_id: str,
        output_dir: Path,
        *,
        range_spec: str = "all",
        options: dict[str, Any] | None = None,
        progress: Callable[[float, str], None] | None = None,
    ) -> list[Path]:
        await asyncio.sleep(5.0)
        return []


@pytest.fixture
def tmp_settings(tmp_path: Path) -> Settings:
    jobs_dir = tmp_path / "jobs"
    outputs_dir = tmp_path / "outputs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    return Settings(data_dir=tmp_path)


def test_corrupted_json_isolation_on_startup(tmp_settings: Settings):
    """验证启动 load_jobs 遇到破损 JSON 时不崩溃，并自动重命名隔离为 .corrupted。"""
    async def _run():
        manager = JobManager(settings=tmp_settings)
        bad_file = tmp_settings.jobs_dir / "bad_task.json"
        bad_file.write_text("{ incomplete_broken_json: ...", encoding="utf-8")

        # 启动加载
        await manager.load_jobs()

        # 校验原 bad.json 已不存在，被安全归档为 bad.json.corrupted
        assert not bad_file.exists()
        corrupted_file = tmp_settings.jobs_dir / "bad_task.json.corrupted"
        assert corrupted_file.exists()
        assert "incomplete_broken_json" in corrupted_file.read_text(encoding="utf-8")

    asyncio.run(_run())


def test_interrupted_job_recovery_on_startup(tmp_settings: Settings):
    """验证服务重启时，之前中断的 running / cancelling 任务自动收敛更新为 failed。"""
    async def _run():
        interrupted_file = tmp_settings.jobs_dir / "job123.json"
        payload = {
            "job_id": "job123",
            "platform": "hongguo",
            "item_id": "item123",
            "status": "running",
            "progress": 50.0,
            "message": "running",
            "files": [],
        }
        interrupted_file.write_text(json.dumps(payload), encoding="utf-8")

        manager = JobManager(settings=tmp_settings)
        await manager.load_jobs()

        record = await manager.get_job("job123")
        assert record is not None
        assert record.status == JobStatus.failed
        assert "服务重启，任务已被中断" in (record.error or "")

    asyncio.run(_run())


def test_graceful_shutdown_cancels_running_tasks(tmp_settings: Settings):
    """验证 manager.shutdown() 能够平滑取消所有未完成任务并释放 Task。"""
    async def _run():
        slow_p = HangMockPlatform()
        with patch("app.jobs.manager.get_platform", return_value=slow_p):
            manager = JobManager(settings=tmp_settings)
            record = await manager.create_job(platform=PlatformName.hongguo, item_id="hang1")
            job_id = record.job_id
            await asyncio.sleep(0.1)

            assert job_id in manager._running_tasks

            # 触发优雅关机
            await manager.shutdown()

            final_record = await manager.get_job(job_id)
            assert final_record is not None
            assert final_record.status == JobStatus.cancelled
            assert job_id not in manager._running_tasks

    asyncio.run(_run())
