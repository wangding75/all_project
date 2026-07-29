"""CQ-03：下载任务生命周期、真正 Task 取消与文件清理测试套件。"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Callable
import pytest

server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

from app.jobs import get_job_manager
from app.models import DetailResponse, JobStatus, PlatformName, SearchItem
from platforms.base import BasePlatform
from unittest.mock import patch
import platforms.registry as registry


class SlowHangingMockPlatform(BasePlatform):
    name = "mock_slow"

    async def search(self, query: str, page: int = 1, **kwargs: Any) -> list[SearchItem]:
        return []

    async def get_detail(self, item_id: str, **kwargs: Any) -> DetailResponse:
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
        # 产生中间临时文件
        tmp_file = output_dir / "partial_download.tmp"
        tmp_file.write_bytes(b"partial_download_content")

        # 模拟耗时或长时间网络阻塞
        await asyncio.sleep(10.0)

        final_file = output_dir / "final.mp4"
        final_file.write_bytes(b"final_content")
        return [final_file]


@pytest.fixture(autouse=True)
def mock_get_platform_slow():
    slow_p = SlowHangingMockPlatform()
    orig_get_platform = registry.get_platform

    def mock_impl(name):
        return slow_p

    with patch("app.jobs.manager.get_platform", side_effect=mock_impl):
        yield


def test_job_cancellation_task_termination_and_cleanup(tmp_path):
    """验证取消任务时真正的 Task 句柄被中断，中间临时文件被物理清理。"""
    async def _run():
        from app.config import Settings
        from app.jobs.manager import JobManager

        manager = JobManager(Settings(data_dir=tmp_path, max_concurrent_jobs=1))

        # 1. 创建慢速下载 Job
        record = await manager.create_job(
            platform=PlatformName.hongguo,
            item_id="item_hang_1",
        )
        job_id = record.job_id

        # 稍微等待确保 _run_job 已进入 download 中的 sleep
        await asyncio.sleep(0.2)

        # 验证任务正在运行且在 _running_tasks 中注册
        assert job_id in manager._running_tasks
        assert manager._running_tasks[job_id].done() is False

        # 2. 执行物理取消
        cancelled_ok = await manager.cancel_job(job_id)
        assert cancelled_ok is True

        # 3. 校验最终状态机
        final_record = await manager.get_job(job_id)
        assert final_record is not None
        assert final_record.status == JobStatus.cancelled
        assert job_id not in manager._running_tasks

        # 4. 校验临时输出目录已清理
        out_dir = manager.settings.outputs_dir / job_id
        assert not out_dir.exists()

    asyncio.run(_run())


def test_job_cancellation_idempotency(tmp_path):
    """验证任务取消具有幂等性，重复取消不报错、不颠覆状态机。"""
    async def _run():
        from app.config import Settings
        from app.jobs.manager import JobManager

        manager = JobManager(Settings(data_dir=tmp_path, max_concurrent_jobs=1))

        record = await manager.create_job(
            platform=PlatformName.hongguo,
            item_id="item_idempotent_1",
        )
        job_id = record.job_id
        await asyncio.sleep(0.1)

        # 第一次取消
        res1 = await manager.cancel_job(job_id)
        assert res1 is True

        # 第二次取消（幂等性）
        res2 = await manager.cancel_job(job_id)
        # 应安全返回 False 或 True，且状态机保持 cancelled
        final_record = await manager.get_job(job_id)
        assert final_record is not None
        assert final_record.status == JobStatus.cancelled

    asyncio.run(_run())
