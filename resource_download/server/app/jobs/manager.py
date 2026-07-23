"""进程内任务队列（MVP-1）。"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.config import Settings, get_settings
from app.models import JobFile, JobResponse, JobStatus, PlatformName
from platforms.registry import get_platform

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.auth import Identity


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class JobRecord:
    job_id: str
    platform: PlatformName
    item_id: str
    range_spec: str
    options: dict[str, Any]
    status: JobStatus = JobStatus.pending
    progress: float = 0.0
    message: str = ""
    error: str | None = None
    files: list[JobFile] = field(default_factory=list)
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    owner_user_id: int | None = None
    owner_kind: str | None = None

    def to_response(self) -> JobResponse:
        extra_dict: dict[str, Any] = {
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.owner_user_id is not None:
            extra_dict["owner_user_id"] = self.owner_user_id
        if self.owner_kind is not None:
            extra_dict["owner_kind"] = self.owner_kind

        return JobResponse(
            job_id=self.job_id,
            platform=self.platform,
            item_id=self.item_id,
            status=self.status,
            progress=self.progress,
            message=self.message,
            error=self.error,
            files=list(self.files),
            extra=extra_dict,
        )


class JobManager:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.settings.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.settings.outputs_dir.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, JobRecord] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    def can_access_job(self, record: JobRecord, identity: Identity) -> bool:
        if identity.is_ops or identity.kind == "api_key":
            return True
        if identity.kind == "user":
            return (
                record.owner_kind == "user"
                and record.owner_user_id is not None
                and record.owner_user_id == identity.user_id
            )
        return False

    def can_access_file(self, file_id: str, identity: Identity) -> bool:
        if identity.is_ops or identity.kind == "api_key":
            return True
        file_id_clean = file_id.strip()
        if not file_id_clean:
            return False
        # Extract potential job_id prefix (e.g. "a1b2c3d4e5f6/file.mp4" -> "a1b2c3d4e5f6")
        job_id_prefix = file_id_clean.split("/")[0].split("\\")[0]
        record = self._jobs.get(job_id_prefix)
        if record is not None:
            return self.can_access_job(record, identity)
        # Search all jobs if file_id matches any JobFile
        for r in self._jobs.values():
            for f in r.files:
                if f.file_id == file_id_clean:
                    return self.can_access_job(r, identity)
        # Disk files without job records: user invisible; ops visible
        return False

    async def load_jobs(self) -> None:
        """从磁盘加载持久化的 Job 记录。若在运行中掉电/重启，则将其置为 failed。若文件坏损，归档为 .corrupted"""
        async with self._lock:
            for file_path in list(self.settings.jobs_dir.glob("*.json")):
                try:
                    data = json.loads(file_path.read_text(encoding="utf-8"))
                    job_id = data.get("job_id")
                    if not job_id:
                        continue
                    status_str = data.get("status", "pending")
                    status = JobStatus(status_str) if status_str in JobStatus.__members__ else JobStatus.failed
                    was_active = status in (JobStatus.pending, JobStatus.running, JobStatus.cancelling)
                    if was_active:
                        status = JobStatus.failed
                        data["error"] = "服务重启，任务已被中断"
                        data["message"] = "failed"
                    
                    files = [JobFile(**f) for f in data.get("files", [])]
                    record = JobRecord(
                        job_id=job_id,
                        platform=PlatformName(data["platform"]),
                        item_id=data["item_id"],
                        range_spec=data.get("range", "all"),
                        options=data.get("options", {}),
                        status=status,
                        progress=float(data.get("progress", 0.0)),
                        message=data.get("message", ""),
                        error=data.get("error"),
                        files=files,
                        created_at=data.get("created_at", _utc_now()),
                        updated_at=data.get("updated_at", _utc_now()),
                        owner_user_id=data.get("owner_user_id"),
                        owner_kind=data.get("owner_kind"),
                    )
                    self._jobs[job_id] = record
                    if was_active:
                        self._persist(record)
                except Exception as exc:  # noqa: BLE001
                    logger.error("读取坏损任务 JSON 文件失败: %s, 错误: %s", file_path, exc)
                    try:
                        corrupted_path = file_path.with_name(file_path.name + ".corrupted")
                        os.replace(file_path, corrupted_path)
                    except Exception:  # noqa: BLE001
                        pass

    async def shutdown(self) -> None:
        """优雅关闭：通知所有运行中的任务取消，等待 Task 结束并持久化最终状态。"""
        async with self._lock:
            running_job_ids = [
                j_id for j_id, j in self._jobs.items()
                if j.status in (JobStatus.pending, JobStatus.running, JobStatus.cancelling)
            ]
        for job_id in running_job_ids:
            await self.cancel_job(job_id)
        logger.info("JobManager 已完成优雅关闭与任务状态持久化")

    async def create_job(
        self,
        platform: PlatformName,
        item_id: str,
        range_spec: str = "all",
        options: dict[str, Any] | None = None,
        max_active: int = 5,
        owner_user_id: int | None = None,
        owner_kind: str | None = None,
    ) -> JobRecord:
        async with self._lock:
            active_count = sum(
                1 for j in self._jobs.values() if j.status in (JobStatus.pending, JobStatus.running)
            )
            if active_count >= max_active:
                raise RuntimeError("active job count limit reached")

            job_id = uuid.uuid4().hex[:12]
            record = JobRecord(
                job_id=job_id,
                platform=platform,
                item_id=item_id,
                range_spec=range_spec or "all",
                options=options or {},
                owner_user_id=owner_user_id,
                owner_kind=owner_kind,
            )
            self._jobs[job_id] = record
            self._evict_old_completed_jobs(max_history_jobs=200)

        await self._persist_async(record)
        task = asyncio.create_task(self._run_job(job_id))
        self._running_tasks[job_id] = task
        return record

    def _evict_old_completed_jobs(self, max_history_jobs: int = 200) -> None:
        """当内存中的 Job 总数超出上限时，安全淘汰最旧的已结束任务。"""
        if len(self._jobs) <= max_history_jobs:
            return

        completed_jobs = [
            j for j in self._jobs.values()
            if j.status in (JobStatus.success, JobStatus.failed, JobStatus.cancelled)
        ]
        if not completed_jobs:
            return

        # 按 updated_at 升序排列（最旧的在前）
        completed_jobs.sort(key=lambda j: j.updated_at)
        overlimit_count = len(self._jobs) - max_history_jobs
        for j in completed_jobs[:overlimit_count]:
            self._jobs.pop(j.job_id, None)

    async def get_job(self, job_id: str) -> JobRecord | None:
        async with self._lock:
            return self._jobs.get(job_id)

    async def get_job_for(self, job_id: str, identity: Identity) -> JobRecord | None:
        async with self._lock:
            record = self._jobs.get(job_id)
            if record is not None and self.can_access_job(record, identity):
                return record
            return None

    async def list_jobs(
        self,
        status: JobStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[JobRecord], int]:
        async with self._lock:
            filtered = list(self._jobs.values())
            if status is not None:
                filtered = [j for j in filtered if j.status == status]
            filtered.sort(key=lambda j: j.created_at, reverse=True)
            total = len(filtered)
            start = (page - 1) * page_size
            end = start + page_size
            return filtered[start:end], total

    async def list_jobs_for(
        self,
        identity: Identity,
        status: JobStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[JobRecord], int]:
        async with self._lock:
            filtered = [j for j in self._jobs.values() if self.can_access_job(j, identity)]
            if status is not None:
                filtered = [j for j in filtered if j.status == status]
            filtered.sort(key=lambda j: j.created_at, reverse=True)
            total = len(filtered)
            start = (page - 1) * page_size
            end = start + page_size
            return filtered[start:end], total

    async def cancel_job(self, job_id: str) -> bool:
        to_persist: JobRecord | None = None
        task_to_cancel: asyncio.Task | None = None
        async with self._lock:
            record = self._jobs.get(job_id)
            if record is not None and record.status in (JobStatus.pending, JobStatus.running, JobStatus.cancelling):
                record.status = JobStatus.cancelling
                record.message = "cancelling"
                record.updated_at = _utc_now()
                to_persist = record
                task_to_cancel = self._running_tasks.get(job_id)

        if task_to_cancel and not task_to_cancel.done():
            task_to_cancel.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(task_to_cancel), timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
                pass

        async with self._lock:
            record = self._jobs.get(job_id)
            if record is not None and record.status == JobStatus.cancelling:
                record.status = JobStatus.cancelled
                record.message = "cancelled"
                record.updated_at = _utc_now()
                to_persist = record

        if to_persist:
            await self._persist_async(to_persist)
            return True
        return False

    async def cancel_job_for(self, job_id: str, identity: Identity) -> bool:
        async with self._lock:
            record = self._jobs.get(job_id)
            if record is None or not self.can_access_job(record, identity):
                return False
        return await self.cancel_job(job_id)

    async def summary(self) -> dict[str, Any]:
        import shutil
        async with self._lock:
            active = sum(1 for j in self._jobs.values() if j.status in (JobStatus.pending, JobStatus.running))
            completed = sum(1 for j in self._jobs.values() if j.status == JobStatus.success)

        try:
            stat = shutil.disk_usage(self.settings.outputs_dir)
            disk_free_human = f"{stat.free / (1024**3):.1f} GB"
        except Exception:  # noqa: BLE001
            disk_free_human = "未知"

        return {
            "active_jobs": active,
            "completed_jobs": completed,
            "total_speed_human": "0.0 MB/s",
            "disk_free_human": disk_free_human,
        }

    async def summary_for(self, identity: Identity) -> dict[str, Any]:
        import shutil
        async with self._lock:
            accessible_jobs = [j for j in self._jobs.values() if self.can_access_job(j, identity)]
            active = sum(1 for j in accessible_jobs if j.status in (JobStatus.pending, JobStatus.running))
            completed = sum(1 for j in accessible_jobs if j.status == JobStatus.success)

        try:
            stat = shutil.disk_usage(self.settings.outputs_dir)
            disk_free_human = f"{stat.free / (1024**3):.1f} GB"
        except Exception:  # noqa: BLE001
            disk_free_human = "未知"

        return {
            "active_jobs": active,
            "completed_jobs": completed,
            "total_speed_human": "0.0 MB/s",
            "disk_free_human": disk_free_human,
        }

    def resolve_file(self, file_id: str) -> Path | None:
        file_id_clean = file_id.strip()
        outputs_root = self.settings.outputs_dir.resolve()
        if not file_id_clean or file_id_clean in (".", "/", "\\"):
            return outputs_root

        for record in self._jobs.values():
            if record.job_id == file_id_clean:
                job_dir = (outputs_root / file_id_clean).resolve()
                if job_dir.exists():
                    return job_dir
            for f in record.files:
                if f.file_id == file_id_clean:
                    path = Path(f.path) if f.path else None
                    if path and path.exists():
                        return path
        # 路径安全校验：防止路径穿越攻击
        candidate = (outputs_root / file_id_clean).resolve()
        if not candidate.is_relative_to(outputs_root):
            return None
        if candidate.exists():
            return candidate
        return None


    async def _update_progress_safe(self, job_id: str, pct: float, msg: str) -> None:
        async with self._lock:
            record = self._jobs.get(job_id)
            if record and record.status == JobStatus.running:
                record.progress = max(0.0, min(100.0, float(pct)))
                record.message = msg
                record.updated_at = _utc_now()

    async def _run_job(self, job_id: str) -> None:
        async with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return
            record.status = JobStatus.running
            record.message = "running"
            record.updated_at = _utc_now()
        await self._persist_async(record)

        out_dir = self.settings.outputs_dir / job_id
        out_dir.mkdir(parents=True, exist_ok=True)

        loop = asyncio.get_running_loop()

        def on_progress(pct: float, msg: str) -> None:
            asyncio.run_coroutine_threadsafe(self._update_progress_safe(job_id, pct, msg), loop)

        try:
            platform = get_platform(record.platform)

            paths = await platform.download(
                record.item_id,
                out_dir,
                range_spec=record.range_spec,
                options=record.options,
                progress=on_progress,
            )

            # 再次检查取消状态
            async with self._lock:
                if record.status in (JobStatus.cancelling, JobStatus.cancelled):
                    return

            files: list[JobFile] = []
            for path in paths:
                path = Path(path)
                rel = f"{job_id}/{path.name}"
                try:
                    rel = str(path.relative_to(self.settings.outputs_dir)).replace("\\", "/")
                except ValueError:
                    rel = f"{job_id}/{path.name}"
                files.append(
                    JobFile(
                        file_id=rel,
                        name=path.name,
                        size=path.stat().st_size if path.is_file() else 0,
                        path=str(path),
                    )
                )
            async with self._lock:
                if record.status not in (JobStatus.cancelling, JobStatus.cancelled):
                    record.status = JobStatus.success
                    record.progress = 100.0
                    record.message = "success"
                    record.files = files
                    record.error = None
                    record.updated_at = _utc_now()
            await self._persist_async(record)
        except asyncio.CancelledError:
            out_dir = self.settings.outputs_dir / job_id
            if out_dir.exists():
                import shutil
                shutil.rmtree(out_dir, ignore_errors=True)
            async with self._lock:
                record = self._jobs.get(job_id)
                if record:
                    record.status = JobStatus.cancelled
                    record.message = "cancelled"
                    record.error = "task cancelled by user"
                    record.updated_at = _utc_now()
                    await self._persist_async(record)
            raise
        except Exception as exc:  # noqa: BLE001 — 任务边界捕获
            async with self._lock:
                record = self._jobs.get(job_id)
                if record and record.status not in (JobStatus.cancelling, JobStatus.cancelled):
                    record.status = JobStatus.failed
                    record.error = str(exc)
                    record.message = "failed"
                    record.updated_at = _utc_now()
                    await self._persist_async(record)
        finally:
            self._running_tasks.pop(job_id, None)

    async def _persist_async(self, record: JobRecord) -> None:
        await asyncio.to_thread(self._persist, record)

    def _persist(self, record: JobRecord) -> None:
        target_path = self.settings.jobs_dir / f"{record.job_id}.json"
        tmp_path = self.settings.jobs_dir / f"{record.job_id}.json.tmp"
        payload = {
            "job_id": record.job_id,
            "platform": record.platform.value,
            "item_id": record.item_id,
            "range": record.range_spec,
            "options": record.options,
            "status": record.status.value,
            "progress": record.progress,
            "message": record.message,
            "error": record.error,
            "files": [f.model_dump() for f in record.files],
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "owner_user_id": record.owner_user_id,
            "owner_kind": record.owner_kind,
        }
        content = json.dumps(payload, ensure_ascii=False, indent=2)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, target_path)


_manager: JobManager | None = None


def get_job_manager() -> JobManager:
    global _manager
    if _manager is None:
        _manager = JobManager()
    return _manager

