"""持久化下载队列与红果上新自动入队测试。"""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.auth import Identity
from app.automation.hongguo_monitor import HongguoMonitorService
from app.config import Settings
from app.jobs.manager import JobManager
from app.models import (
    DiscoverItem,
    HongguoMonitorConfig,
    JobStatus,
    PlatformName,
)


class _ControlledPlatform:
    def __init__(self) -> None:
        self.started: list[str] = []
        self.gates: dict[str, asyncio.Event] = {}

    async def download(self, item_id, output_dir, **_kwargs):
        self.started.append(str(item_id))
        gate = self.gates.setdefault(str(item_id), asyncio.Event())
        await gate.wait()
        output = Path(output_dir) / f"{item_id}.mp4"
        output.write_bytes(b"playable")
        return [output]


def test_queue_pause_reorder_and_resume(tmp_path, monkeypatch):
    from app.jobs import manager as manager_module

    async def _run():
        settings = Settings(
            data_dir=tmp_path,
            max_concurrent_jobs=1,
            max_queued_jobs=10,
        )
        platform = _ControlledPlatform()
        monkeypatch.setattr(manager_module, "get_platform", lambda _name: platform)
        manager = JobManager(settings)
        identity = Identity(kind="api_key", is_ops=True)

        first = await manager.create_job(PlatformName.hongguo, "first")
        second = await manager.create_job(PlatformName.hongguo, "second")
        third = await manager.create_job(PlatformName.hongguo, "third")
        await asyncio.sleep(0.05)

        assert platform.started == ["first"]
        assert (await manager.get_job(second.job_id)).status == JobStatus.pending
        assert await manager.pause_queue_for(identity) == 2
        assert (await manager.get_job(second.job_id)).status == JobStatus.paused

        assert await manager.reorder_queue_for(
            identity,
            [third.job_id, second.job_id],
        )
        queue = await manager.queue_state_for(identity)
        queued_ids = [
            item.job_id for item in queue["items"] if item.status == JobStatus.paused
        ]
        assert queued_ids == [third.job_id, second.job_id]

        assert await manager.resume_queue_for(identity) == 2
        await manager.cancel_job(first.job_id)
        await asyncio.sleep(0.05)
        assert platform.started == ["first", "third"]

        platform.gates["third"].set()
        await asyncio.sleep(0.05)
        platform.gates.setdefault("second", asyncio.Event()).set()
        await asyncio.sleep(0.05)
        assert (await manager.get_job(third.job_id)).status == JobStatus.success
        assert (await manager.get_job(second.job_id)).status == JobStatus.success
        await manager.shutdown()

    asyncio.run(_run())


def test_hongguo_monitor_baselines_then_enqueues_only_new_items(
    tmp_path,
    monkeypatch,
):
    from app.automation import hongguo_monitor as monitor_module
    from app.jobs import manager as manager_module

    class _DiscoverAndDownload:
        def __init__(self):
            self.rows = [
                DiscoverItem(
                    id="old-1",
                    title="已有短剧",
                    platform=PlatformName.hongguo,
                )
            ]

        async def discover(self, _kind, *, limit=50):
            return self.rows[:limit]

        async def download(self, item_id, output_dir, **_kwargs):
            output = Path(output_dir) / f"{item_id}.mp4"
            output.write_bytes(b"playable")
            return [output]

    async def _run():
        settings = Settings(
            data_dir=tmp_path,
            max_concurrent_jobs=1,
            max_queued_jobs=10,
        )
        platform = _DiscoverAndDownload()
        monkeypatch.setattr(monitor_module, "get_platform", lambda _name: platform)
        monkeypatch.setattr(manager_module, "get_platform", lambda _name: platform)
        manager = JobManager(settings)
        class _ActiveGateway:
            def check_device_entitlement(self, _device_id):
                return {
                    "decision": "ACTIVE",
                    "reason": "ACTIVE",
                    "activated": True,
                }

        import app.db as db_module
        import app.quota as quota_module

        class _Db:
            def query(self, *_args):
                return self

            def filter(self, *_args):
                return self

            def first(self):
                return type("UserRow", (), {"is_active": True})()

            def close(self):
                pass

        monkeypatch.setattr(db_module, "SessionLocal", lambda: _Db())
        monkeypatch.setattr(quota_module, "check_job_quota", lambda *_args: None)
        monkeypatch.setattr(quota_module, "increment_job_quota", lambda *_args: None)
        service = HongguoMonitorService(settings, manager, _ActiveGateway())
        identity = Identity(kind="user", user_id=1)
        await service.configure(
            identity,
            HongguoMonitorConfig(
                enabled=False,
                auto_enqueue=True,
                min_episode_count=10,
                exclude_keywords=["忽略"],
                max_auto_enqueue_per_scan=1,
            ),
            verified_device_id="dev_" + "1" * 64,
        )

        baseline = await service.scan_now(identity)
        assert baseline.baseline_initialized is True
        assert baseline.last_detected_count == 0
        jobs, total = await manager.list_jobs_for(identity, page_size=100)
        assert total == 0

        platform.rows.append(
            DiscoverItem(
                id="new-2",
                title="刚上新的短剧",
                platform=PlatformName.hongguo,
                extra={"episode_count": 24},
            )
        )
        platform.rows.append(
            DiscoverItem(
                id="ignored-3",
                title="忽略这条上新",
                platform=PlatformName.hongguo,
                extra={"episode_count": 30},
            )
        )
        detected = await service.scan_now(identity)
        assert detected.last_detected_count == 1
        assert detected.total_enqueued_count == 1
        assert detected.recent_items[0].id == "new-2"
        assert detected.logs[-1].detected == 1
        assert "过滤 1 条" in detected.logs[-1].message
        await asyncio.sleep(0.05)
        jobs, total = await manager.list_jobs_for(identity, page_size=100)
        assert total == 1
        assert jobs[0].item_id == "new-2"
        assert jobs[0].options["source"] == "hongguo_new_monitor"
        await service.stop()
        await manager.shutdown()

    asyncio.run(_run())


def test_paused_queue_keeps_new_and_retried_jobs_paused(tmp_path):
    async def _run():
        settings = Settings(
            data_dir=tmp_path,
            max_concurrent_jobs=1,
            max_queued_jobs=10,
        )
        manager = JobManager(settings)
        identity = Identity(kind="api_key", is_ops=True)
        await manager.pause_queue_for(identity)

        fresh = await manager.create_job(PlatformName.hongguo, "fresh")
        assert fresh.status == JobStatus.paused

        fresh.status = JobStatus.failed
        fresh.error = "temporary failure"
        retried = await manager.retry_job_for(fresh.job_id, identity)
        assert retried is not None
        assert retried.status == JobStatus.paused
        assert retried.error is None
        assert manager._running_tasks == {}
        await manager.shutdown()

    asyncio.run(_run())


def test_selected_queue_actions_and_archive_keep_file_authorization(tmp_path):
    async def _run():
        settings = Settings(
            data_dir=tmp_path,
            max_concurrent_jobs=1,
            max_queued_jobs=10,
        )
        manager = JobManager(settings)
        identity = Identity(kind="api_key", is_ops=True)
        await manager.pause_queue_for(identity)
        first = await manager.create_job(PlatformName.hongguo, "first")
        second = await manager.create_job(PlatformName.hongguo, "second")
        manager._closing = True
        manager._paused_owners.clear()
        first.status = JobStatus.pending
        first.pause_scope = ""
        second.status = JobStatus.pending
        second.pause_scope = ""

        changed, skipped = await manager.set_jobs_paused_for(
            identity,
            [first.job_id],
            paused=True,
        )
        assert changed == [first.job_id]
        assert skipped == []
        assert (await manager.get_job(first.job_id)).pause_scope == "item"
        assert (await manager.get_job(second.job_id)).status == JobStatus.pending

        resumed, skipped = await manager.set_jobs_paused_for(
            identity,
            [first.job_id, "missing"],
            paused=False,
        )
        assert resumed == [first.job_id]
        assert skipped == ["missing"]

        await manager.cancel_job(first.job_id)
        archived, skipped = await manager.archive_jobs_for(
            identity,
            [first.job_id, second.job_id],
        )
        assert archived == [first.job_id]
        assert skipped == [second.job_id]
        visible, total = await manager.list_jobs_for(identity, page_size=20)
        assert total == 1
        assert visible[0].job_id == second.job_id
        assert await manager.get_job_for(first.job_id, identity) is not None
        await manager.shutdown()

    asyncio.run(_run())
