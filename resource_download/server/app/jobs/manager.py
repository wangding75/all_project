"""进程内任务队列（MVP-1）。"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.config import Settings, get_settings
from app.errors import format_platform_error, sanitize_error_text
from app.models import JobFile, JobResponse, JobStatus, PlatformName
from app.options import sanitize_persisted_options, split_job_options, validate_range_spec
from platforms.registry import get_platform

logger = logging.getLogger(__name__)

LEGACY_UNOWNED_OWNER_KIND = "legacy_unowned"
JOB_PERSISTENCE_VERSION = 2

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
    license_id: str | None = None
    device_id: str | None = None
    legacy_unowned: bool = False
    queue_position: int = 0
    archived: bool = False
    pause_scope: str = ""
    # Per-job secrets (for example a Fanqie cookie) are intentionally kept in
    # memory only and are never serialized to the job JSON file.
    runtime_options: dict[str, Any] = field(default_factory=dict, repr=False)
    # Non-secret marker used to report REAUTH after a restart.  Values are
    # deliberately capability names, not client-supplied secret names.
    runtime_requirements: set[str] = field(default_factory=set, repr=False)

    def to_response(self) -> JobResponse:
        extra_dict: dict[str, Any] = {
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.owner_user_id is not None:
            extra_dict["owner_user_id"] = self.owner_user_id
        if self.owner_kind is not None:
            extra_dict["owner_kind"] = self.owner_kind
        if self.license_id is not None:
            extra_dict["license_id"] = self.license_id
        if self.device_id is not None:
            extra_dict["device_id"] = self.device_id
        if self.legacy_unowned:
            extra_dict["legacy_unowned"] = True
        extra_dict["queue_position"] = self.queue_position
        extra_dict["archived"] = self.archived
        if self.pause_scope:
            extra_dict["pause_scope"] = self.pause_scope
        # 客户端建任务时传入的书名/剧名
        if isinstance(self.options, dict):
            title = self.options.get("title")
            if title:
                extra_dict["title"] = str(title)

        outputs_root = get_settings().outputs_dir.resolve()
        safe_files: list[JobFile] = []
        for job_file in self.files:
            file_owner = {
                "owner_kind": self.owner_kind,
                "owner_user_id": self.owner_user_id,
                "license_id": self.license_id,
                "device_id": self.device_id,
                "legacy_unowned": self.legacy_unowned,
            }
            if not job_file.path:
                safe_files.append(job_file.model_copy(update=file_owner))
                continue
            try:
                candidate = Path(job_file.path).resolve()
                if candidate.is_relative_to(outputs_root):
                    safe_files.append(job_file.model_copy(update=file_owner))
                else:
                    safe_files.append(job_file.model_copy(update={"path": None, **file_owner}))
            except OSError:
                safe_files.append(job_file.model_copy(update={"path": None, **file_owner}))

        return JobResponse(
            job_id=self.job_id,
            platform=self.platform,
            item_id=self.item_id,
            status=self.status,
            progress=self.progress,
            message=self.message,
            error=self.error,
            files=safe_files,
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
        self._persist_lock = threading.Lock()
        self._speed_samples: dict[str, tuple[float, int]] = {}
        self._queue_counter = 0
        self._paused_owners: set[str] = set()
        self._dispatcher_task: asyncio.Task | None = None
        self._queue_changed = asyncio.Event()
        self._closing = False

    def can_access_job(self, record: JobRecord, identity: Identity) -> bool:
        if identity.is_ops or identity.kind == "api_key":
            return True
        if record.owner_kind == "license_device":
            return (
                bool(identity.license_id)
                and bool(identity.device_id)
                and record.license_id == identity.license_id
                and record.device_id == identity.device_id
            )
        if identity.kind == "user":
            return (
                record.owner_kind == "user"
                and record.owner_user_id is not None
                and record.owner_user_id == identity.user_id
            )
        return False

    @staticmethod
    def _owner_key(
        owner_kind: str | None,
        owner_user_id: int | None,
        license_id: str | None = None,
        device_id: str | None = None,
    ) -> str:
        if owner_kind == "license_device" and license_id and device_id:
            return f"license:{license_id}:device:{device_id}"
        if owner_kind == "user" and owner_user_id is not None:
            return f"user:{owner_user_id}"
        return "ops"

    @staticmethod
    def _identity_owner_key(identity: Identity) -> str:
        if identity.license_id and identity.device_id:
            return f"license:{identity.license_id}:device:{identity.device_id}"
        if identity.kind == "user" and identity.user_id is not None:
            return f"user:{identity.user_id}"
        return "ops"

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
                    was_active = status in (JobStatus.running, JobStatus.cancelling)
                    if was_active:
                        status = JobStatus.failed
                        data["error"] = "服务重启，任务已被中断"
                        data["message"] = "failed"
                    
                    outputs_root = self.settings.outputs_dir.resolve()
                    files: list[JobFile] = []
                    for raw_file in data.get("files", []):
                        try:
                            job_file = JobFile(**raw_file)
                        except Exception:
                            continue
                        if job_file.path:
                            try:
                                stored_path = Path(job_file.path).resolve()
                                if not stored_path.is_relative_to(outputs_root):
                                    # Never rehydrate an arbitrary path from
                                    # untrusted/persisted JSON.
                                    job_file.path = None
                            except OSError:
                                job_file.path = None
                        files.append(job_file)
                    license_id = str(data.get("license_id") or "").strip() or None
                    device_id = str(data.get("device_id") or "").strip() or None
                    owner_kind = str(data.get("owner_kind") or "").strip() or None
                    legacy_unowned = bool(data.get("legacy_unowned"))
                    # A historical JSON job can only be re-owned when both
                    # License subject fields were durably persisted together.
                    # Never infer a License from a User/JWT or from a filename.
                    if not (license_id and device_id and owner_kind == "license_device"):
                        legacy_unowned = True
                        owner_kind = LEGACY_UNOWNED_OWNER_KIND
                    file_owner_migration_needed = any(
                        not isinstance(raw_file, dict)
                        or raw_file.get("owner_kind") != owner_kind
                        or raw_file.get("owner_user_id") != data.get("owner_user_id")
                        or raw_file.get("license_id") != license_id
                        or raw_file.get("device_id") != device_id
                        or bool(raw_file.get("legacy_unowned")) != legacy_unowned
                        for raw_file in (data.get("files") or [])
                    )
                    record = JobRecord(
                        job_id=job_id,
                        platform=PlatformName(data["platform"]),
                        item_id=data["item_id"],
                        range_spec=data.get("range", "all"),
                        options=sanitize_persisted_options(data.get("options", {})),
                        status=status,
                        progress=float(data.get("progress", 0.0)),
                        message=data.get("message", ""),
                        error=sanitize_error_text(data.get("error")) if data.get("error") else None,
                        files=files,
                        created_at=data.get("created_at", _utc_now()),
                        updated_at=data.get("updated_at", _utc_now()),
                        owner_user_id=data.get("owner_user_id"),
                        owner_kind=owner_kind,
                        license_id=license_id,
                        device_id=device_id,
                        legacy_unowned=legacy_unowned,
                        queue_position=int(data.get("queue_position") or 0),
                        archived=bool(data.get("archived", False)),
                        pause_scope=str(data.get("pause_scope") or ""),
                        runtime_requirements={
                            str(item)
                            for item in (data.get("runtime_requirements") or [])
                            if isinstance(item, str)
                        },
                    )
                    record.files = [
                        job_file.model_copy(
                            update={
                                "owner_kind": record.owner_kind,
                                "owner_user_id": record.owner_user_id,
                                "license_id": record.license_id,
                                "device_id": record.device_id,
                                "legacy_unowned": record.legacy_unowned,
                            }
                        )
                        for job_file in record.files
                    ]
                    if record.queue_position <= 0:
                        self._queue_counter += 1
                        record.queue_position = self._queue_counter
                    else:
                        self._queue_counter = max(self._queue_counter, record.queue_position)
                    self._jobs[job_id] = record
                    if record.status == JobStatus.paused and record.pause_scope != "item":
                        self._paused_owners.add(
                            self._owner_key(
                                record.owner_kind,
                                record.owner_user_id,
                                record.license_id,
                                record.device_id,
                            )
                        )
                    if (
                        was_active
                        or not data.get("queue_position")
                        or data.get("persistence_version") != JOB_PERSISTENCE_VERSION
                        or data.get("owner_kind") != record.owner_kind
                        or bool(data.get("legacy_unowned")) != record.legacy_unowned
                        or file_owner_migration_needed
                    ):
                        self._persist(record)
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "读取坏损任务 JSON 文件失败: %s, 错误: %s",
                        file_path.name,
                        sanitize_error_text(exc),
                    )
                    try:
                        corrupted_path = file_path.with_name(file_path.name + ".corrupted")
                        os.replace(file_path, corrupted_path)
                    except Exception:  # noqa: BLE001
                        pass
        self._evict_old_completed_jobs()
        self._ensure_dispatcher()
        self._queue_changed.set()

    async def shutdown(self) -> None:
        """优雅关闭：通知所有运行中的任务取消，等待 Task 结束并持久化最终状态。"""
        self._closing = True
        self._queue_changed.set()
        if self._dispatcher_task and not self._dispatcher_task.done():
            self._dispatcher_task.cancel()
            try:
                await self._dispatcher_task
            except asyncio.CancelledError:
                pass
        async with self._lock:
            running_job_ids = [
                j_id for j_id, j in self._jobs.items()
                if j.status in (JobStatus.running, JobStatus.cancelling)
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
        max_active: int | None = None,
        owner_user_id: int | None = None,
        owner_kind: str | None = None,
        license_id: str | None = None,
        device_id: str | None = None,
        priority: bool = False,
    ) -> JobRecord:
        persisted_options, runtime_options = split_job_options(platform, options)
        range_spec = validate_range_spec(range_spec)
        # TestClient / embedded 模式可能在同一进程内完成一次 shutdown 后重新启动。
        if self._closing:
            self._closing = False
            self._dispatcher_task = None
        async with self._lock:
            active_count = sum(
                1
                for j in self._jobs.values()
                if j.status in (JobStatus.pending, JobStatus.paused, JobStatus.running)
            )
            queue_limit = max_active or self.settings.max_queued_jobs
            if active_count >= queue_limit:
                raise RuntimeError("job queue capacity reached")

            job_id = uuid.uuid4().hex[:12]
            if priority:
                queue_position = min(
                    (
                        job.queue_position
                        for job in self._jobs.values()
                        if job.status in (JobStatus.pending, JobStatus.paused)
                    ),
                    default=1,
                ) - 1
            else:
                queue_position = self._queue_counter + 1
            record = JobRecord(
                job_id=job_id,
                platform=platform,
                item_id=item_id,
                range_spec=range_spec or "all",
                options=persisted_options,
                runtime_options=runtime_options,
                runtime_requirements={
                    "fanqie_session" if name == "cookie" else str(name)
                    for name in runtime_options
                },
                owner_user_id=owner_user_id,
                owner_kind=owner_kind,
                license_id=license_id,
                device_id=device_id,
                queue_position=queue_position,
                status=(
                    JobStatus.paused
                    if self._owner_key(owner_kind, owner_user_id, license_id, device_id)
                    in self._paused_owners
                    else JobStatus.pending
                ),
            )
            if record.status == JobStatus.paused:
                record.message = "queue paused"
                record.pause_scope = "queue"
            self._queue_counter = max(self._queue_counter + 1, queue_position)
            self._jobs[job_id] = record
            self._evict_old_completed_jobs(max_history_jobs=200)

        await self._persist_async(record)
        from app.logger import metrics_tracker

        metrics_tracker.record_job_created(platform.value)
        self._ensure_dispatcher()
        self._queue_changed.set()
        return record

    def _ensure_dispatcher(self) -> None:
        if self._closing:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        if self._dispatcher_task is None or self._dispatcher_task.done():
            self._dispatcher_task = loop.create_task(self._dispatch_loop())

    async def _dispatch_loop(self) -> None:
        while not self._closing:
            await self._queue_changed.wait()
            self._queue_changed.clear()
            while not self._closing:
                async with self._lock:
                    running_count = sum(
                        1 for job in self._jobs.values() if job.status == JobStatus.running
                    )
                    capacity = max(1, self.settings.max_concurrent_jobs) - running_count
                    if capacity <= 0:
                        break
                    pending = sorted(
                        (
                            job
                            for job in self._jobs.values()
                            if job.status == JobStatus.pending
                        ),
                        key=lambda job: (job.queue_position, job.created_at),
                    )
                    if not pending:
                        break
                    selected = pending[:capacity]
                    for record in selected:
                        record.status = JobStatus.running
                        record.message = "running"
                        record.updated_at = _utc_now()
                        task = asyncio.create_task(self._run_job(record.job_id))
                        self._running_tasks[record.job_id] = task
                for record in selected:
                    await self._persist_async(record)

    def _evict_old_completed_jobs(self, max_history_jobs: int = 200) -> None:
        """当内存中的 Job 总数超出上限时，安全淘汰最旧的已结束任务。"""
        max_history_jobs = max(1, int(getattr(self.settings, "max_history_jobs", max_history_jobs)))
        completed_jobs = [
            j
            for j in self._jobs.values()
            if j.status in (JobStatus.success, JobStatus.failed, JobStatus.cancelled)
        ]
        active_count = len(self._jobs) - len(completed_jobs)
        terminal_limit = max(0, max_history_jobs - active_count)
        if len(completed_jobs) <= terminal_limit:
            return
        if not completed_jobs:
            return

        # 按 updated_at 升序排列（最旧的在前）
        completed_jobs.sort(key=lambda j: j.updated_at)
        overlimit_count = len(completed_jobs) - terminal_limit
        for j in completed_jobs[:overlimit_count]:
            self._jobs.pop(j.job_id, None)
            try:
                (self.settings.jobs_dir / f"{j.job_id}.json").unlink(missing_ok=True)
            except OSError:
                pass
            # A terminal record and its output are one retention unit.  This
            # prevents an otherwise unbounded outputs directory after the
            # in-memory history has been evicted.
            try:
                import shutil

                output_root = self.settings.outputs_dir.resolve()
                job_dir = (output_root / j.job_id).resolve()
                if job_dir.is_relative_to(output_root):
                    shutil.rmtree(job_dir, ignore_errors=True)
            except OSError:
                pass

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
            filtered = [job for job in self._jobs.values() if not job.archived]
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
            filtered = [
                j
                for j in self._jobs.values()
                if self.can_access_job(j, identity) and not j.archived
            ]
            if status is not None:
                filtered = [j for j in filtered if j.status == status]
            filtered.sort(key=lambda j: j.created_at, reverse=True)
            total = len(filtered)
            start = (page - 1) * page_size
            end = start + page_size
            return filtered[start:end], total

    async def queue_state_for(self, identity: Identity) -> dict[str, Any]:
        async with self._lock:
            items = [
                job
                for job in self._jobs.values()
                if self.can_access_job(job, identity)
                and not job.archived
                and job.status in (JobStatus.pending, JobStatus.paused, JobStatus.running)
            ]
            items.sort(
                key=lambda job: (
                    0 if job.status == JobStatus.running else 1,
                    job.queue_position,
                    job.created_at,
                )
            )
            return {
                "paused": self._identity_owner_key(identity) in self._paused_owners,
                "max_concurrent_jobs": max(1, self.settings.max_concurrent_jobs),
                "running_count": sum(job.status == JobStatus.running for job in items),
                "pending_count": sum(
                    job.status in (JobStatus.pending, JobStatus.paused) for job in items
                ),
                "items": [job.to_response() for job in items],
            }

    async def pause_queue_for(self, identity: Identity) -> int:
        changed: list[JobRecord] = []
        async with self._lock:
            self._paused_owners.add(self._identity_owner_key(identity))
            for record in self._jobs.values():
                if record.status == JobStatus.pending and self.can_access_job(record, identity):
                    record.status = JobStatus.paused
                    record.message = "queue paused"
                    record.pause_scope = "queue"
                    record.updated_at = _utc_now()
                    changed.append(record)
        for record in changed:
            await self._persist_async(record)
        return len(changed)

    async def resume_queue_for(self, identity: Identity) -> int:
        changed: list[JobRecord] = []
        async with self._lock:
            self._paused_owners.discard(self._identity_owner_key(identity))
            for record in self._jobs.values():
                if record.status == JobStatus.paused and self.can_access_job(record, identity):
                    record.status = JobStatus.pending
                    record.message = "queued"
                    record.pause_scope = ""
                    record.updated_at = _utc_now()
                    changed.append(record)
        for record in changed:
            await self._persist_async(record)
        if changed:
            self._ensure_dispatcher()
            self._queue_changed.set()
        return len(changed)

    async def reorder_queue_for(self, identity: Identity, job_ids: list[str]) -> bool:
        requested = list(dict.fromkeys(job_ids))
        async with self._lock:
            movable = [
                job
                for job in self._jobs.values()
                if self.can_access_job(job, identity)
                and job.status in (JobStatus.pending, JobStatus.paused)
            ]
            movable_by_id = {job.job_id: job for job in movable}
            if any(job_id not in movable_by_id for job_id in requested):
                return False
            remaining = sorted(
                (job for job in movable if job.job_id not in requested),
                key=lambda job: (job.queue_position, job.created_at),
            )
            ordered = [movable_by_id[job_id] for job_id in requested] + remaining
            # 用户只能在自己原先占有的队列位置槽内重排，不能插队到其他用户之前。
            positions = sorted(job.queue_position for job in movable)
            for position, record in zip(positions, ordered, strict=True):
                record.queue_position = position
                record.updated_at = _utc_now()
            changed = list(ordered)
            self._queue_counter = max(
                self._queue_counter,
                max((job.queue_position for job in self._jobs.values()), default=0),
            )
        for record in changed:
            await self._persist_async(record)
        self._queue_changed.set()
        return True

    async def retry_job_for(self, job_id: str, identity: Identity) -> JobRecord | None:
        async with self._lock:
            record = self._jobs.get(job_id)
            if (
                record is None
                or not self.can_access_job(record, identity)
                or record.status not in (JobStatus.failed, JobStatus.cancelled)
            ):
                return None
            self._queue_counter += 1
            record.status = (
                JobStatus.paused
                if self._owner_key(
                    record.owner_kind,
                    record.owner_user_id,
                    record.license_id,
                    record.device_id,
                )
                in self._paused_owners
                else JobStatus.pending
            )
            record.pause_scope = "queue" if record.status == JobStatus.paused else ""
            record.progress = 0.0
            record.message = "queued for retry"
            record.error = None
            record.files = []
            record.archived = False
            record.queue_position = self._queue_counter
            record.updated_at = _utc_now()
        output_dir = self.settings.outputs_dir / job_id
        if output_dir.exists():
            import shutil

            await asyncio.to_thread(shutil.rmtree, output_dir, True)
        await self._persist_async(record)
        from app.logger import metrics_tracker

        metrics_tracker.record_job_created(record.platform.value)
        self._ensure_dispatcher()
        self._queue_changed.set()
        return record

    async def cancel_job(self, job_id: str) -> bool:
        to_persist: JobRecord | None = None
        task_to_cancel: asyncio.Task | None = None
        async with self._lock:
            record = self._jobs.get(job_id)
            if record is not None and record.status in (
                JobStatus.pending,
                JobStatus.paused,
                JobStatus.running,
                JobStatus.cancelling,
            ):
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
            self._queue_changed.set()
            return True
        return False

    async def cancel_job_for(self, job_id: str, identity: Identity) -> bool:
        async with self._lock:
            record = self._jobs.get(job_id)
            if record is None or not self.can_access_job(record, identity):
                return False
        return await self.cancel_job(job_id)

    async def set_jobs_paused_for(
        self,
        identity: Identity,
        job_ids: list[str],
        *,
        paused: bool,
    ) -> tuple[list[str], list[str]]:
        """Pause/resume selected waiting jobs without changing the whole owner queue."""
        requested = list(dict.fromkeys(job_ids))
        changed: list[JobRecord] = []
        skipped: list[str] = []
        owner_paused = self._identity_owner_key(identity) in self._paused_owners
        async with self._lock:
            for job_id in requested:
                record = self._jobs.get(job_id)
                if record is None or not self.can_access_job(record, identity):
                    skipped.append(job_id)
                    continue
                if paused and record.status == JobStatus.pending:
                    record.status = JobStatus.paused
                    record.message = "paused by user"
                    record.pause_scope = "item"
                elif not paused and record.status == JobStatus.paused and not owner_paused:
                    record.status = JobStatus.pending
                    record.message = "queued"
                    record.pause_scope = ""
                else:
                    skipped.append(job_id)
                    continue
                record.updated_at = _utc_now()
                changed.append(record)
        for record in changed:
            await self._persist_async(record)
        if changed:
            self._ensure_dispatcher()
            self._queue_changed.set()
        return [record.job_id for record in changed], skipped

    async def archive_jobs_for(
        self,
        identity: Identity,
        job_ids: list[str],
    ) -> tuple[list[str], list[str]]:
        """Hide terminal jobs from history while retaining records for file authorization."""
        requested = list(dict.fromkeys(job_ids))
        changed: list[JobRecord] = []
        skipped: list[str] = []
        async with self._lock:
            for job_id in requested:
                record = self._jobs.get(job_id)
                if (
                    record is None
                    or not self.can_access_job(record, identity)
                    or record.status
                    not in (JobStatus.success, JobStatus.failed, JobStatus.cancelled)
                ):
                    skipped.append(job_id)
                    continue
                record.archived = True
                record.updated_at = _utc_now()
                changed.append(record)
        for record in changed:
            await self._persist_async(record)
        return [record.job_id for record in changed], skipped

    async def summary(self) -> dict[str, Any]:
        import shutil
        async with self._lock:
            active = sum(
                1
                for j in self._jobs.values()
                if j.status in (JobStatus.pending, JobStatus.paused, JobStatus.running)
            )
            completed = sum(1 for j in self._jobs.values() if j.status == JobStatus.success)

        try:
            stat = shutil.disk_usage(self.settings.outputs_dir)
            disk_free_human = f"{stat.free / (1024**3):.1f} GB"
        except Exception:  # noqa: BLE001
            disk_free_human = "未知"

        speed = await asyncio.to_thread(
            self._measure_speed,
            "ops",
            [job.job_id for job in self._jobs.values()],
        )
        return {
            "active_jobs": active,
            "completed_jobs": completed,
            "total_speed_human": self._format_speed(speed),
            "disk_free_human": disk_free_human,
        }

    async def summary_for(self, identity: Identity) -> dict[str, Any]:
        import shutil
        async with self._lock:
            accessible_jobs = [
                j
                for j in self._jobs.values()
                if self.can_access_job(j, identity) and not j.archived
            ]
            active = sum(
                1
                for j in accessible_jobs
                if j.status in (JobStatus.pending, JobStatus.paused, JobStatus.running)
            )
            completed = sum(1 for j in accessible_jobs if j.status == JobStatus.success)

        try:
            stat = shutil.disk_usage(self.settings.outputs_dir)
            disk_free_human = f"{stat.free / (1024**3):.1f} GB"
        except Exception:  # noqa: BLE001
            disk_free_human = "未知"

        speed_key = (
            f"user:{identity.user_id}"
            if identity.kind == "user"
            else f"{identity.kind}:ops"
        )
        speed = await asyncio.to_thread(
            self._measure_speed,
            speed_key,
            [job.job_id for job in accessible_jobs],
        )
        return {
            "active_jobs": active,
            "completed_jobs": completed,
            "total_speed_human": self._format_speed(speed),
            "disk_free_human": disk_free_human,
        }

    def _measure_speed(self, key: str, job_ids: list[str]) -> float:
        total_bytes = 0
        for job_id in job_ids:
            job_dir = self.settings.outputs_dir / job_id
            if not job_dir.is_dir():
                continue
            try:
                total_bytes += sum(
                    path.stat().st_size
                    for path in job_dir.rglob("*")
                    if path.is_file()
                )
            except OSError:
                continue
        now = time.monotonic()
        previous = self._speed_samples.get(key)
        self._speed_samples[key] = (now, total_bytes)
        if previous is None or now <= previous[0] or total_bytes < previous[1]:
            return 0.0
        return (total_bytes - previous[1]) / (now - previous[0])

    @staticmethod
    def _format_speed(bytes_per_second: float) -> str:
        if bytes_per_second >= 1024**2:
            return f"{bytes_per_second / (1024**2):.1f} MB/s"
        if bytes_per_second >= 1024:
            return f"{bytes_per_second / 1024:.1f} KB/s"
        return f"{bytes_per_second:.0f} B/s"

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
                    path = Path(f.path).resolve() if f.path else None
                    if (
                        path
                        and path.exists()
                        and path.is_relative_to(outputs_root)
                    ):
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
        try:
            async with self._lock:
                record = self._jobs.get(job_id)
                if record is None or record.status != JobStatus.running:
                    return
            out_dir = self.settings.outputs_dir / job_id
            out_dir.mkdir(parents=True, exist_ok=True)

            loop = asyncio.get_running_loop()

            def on_progress(pct: float, msg: str) -> None:
                asyncio.run_coroutine_threadsafe(self._update_progress_safe(job_id, pct, msg), loop)
            missing_runtime = [
                name
                for name in record.runtime_requirements
                if (name == "fanqie_session" and "cookie" not in record.runtime_options)
                or (name != "fanqie_session" and name not in record.runtime_options)
            ]
            if missing_runtime:
                if "fanqie_session" in missing_runtime:
                    raise RuntimeError("COOKIE_REQUIRED: runtime Fanqie session must be supplied again")
                raise RuntimeError("REAUTH_REQUIRED: runtime credentials must be supplied again")
            platform = get_platform(record.platform)

            paths = await platform.download(
                record.item_id,
                out_dir,
                range_spec=record.range_spec,
                options={**record.options, **record.runtime_options},
                progress=on_progress,
            )

            # 再次检查取消状态
            async with self._lock:
                if record.status in (JobStatus.cancelling, JobStatus.cancelled):
                    return

            files: list[JobFile] = []
            for path in paths:
                path = Path(path)
                try:
                    resolved_path = path.resolve(strict=True)
                except (FileNotFoundError, OSError) as exc:
                    raise RuntimeError("download adapter returned a missing output file") from exc
                outputs_root = self.settings.outputs_dir.resolve()
                if not resolved_path.is_file() or not resolved_path.is_relative_to(outputs_root):
                    raise RuntimeError("download adapter returned a path outside outputs_dir")
                path = resolved_path
                rel = str(path.relative_to(outputs_root)).replace("\\", "/")
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
            from app.logger import metrics_tracker

            metrics_tracker.record_job_success(record.platform.value)
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
                    record.error = format_platform_error(exc)
                    record.message = "failed"
                    record.updated_at = _utc_now()
                    await self._persist_async(record)
                    from app.logger import metrics_tracker

                    metrics_tracker.record_job_failed(record.platform.value)
        finally:
            self._running_tasks.pop(job_id, None)
            self._queue_changed.set()

    async def _persist_async(self, record: JobRecord) -> None:
        await asyncio.to_thread(self._persist, record)

    def _persist(self, record: JobRecord) -> None:
        target_path = self.settings.jobs_dir / f"{record.job_id}.json"
        tmp_path = self.settings.jobs_dir / f"{record.job_id}.json.tmp"
        with self._persist_lock:
            # 在互斥区内读取可变 JobRecord，避免较旧快照后写覆盖较新状态。
            outputs_root = self.settings.outputs_dir.resolve()
            persisted_files: list[dict[str, Any]] = []
            for job_file in record.files:
                file_data = job_file.model_dump()
                file_data.update(
                    {
                        "owner_kind": record.owner_kind,
                        "owner_user_id": record.owner_user_id,
                        "license_id": record.license_id,
                        "device_id": record.device_id,
                        "legacy_unowned": record.legacy_unowned,
                    }
                )
                if file_data.get("path"):
                    try:
                        stored_path = Path(str(file_data["path"])).resolve()
                        if not stored_path.is_relative_to(outputs_root):
                            file_data["path"] = None
                    except OSError:
                        file_data["path"] = None
                persisted_files.append(file_data)
            payload = {
                "job_id": record.job_id,
                "platform": record.platform.value,
                "item_id": record.item_id,
                "range": record.range_spec,
                "options": sanitize_persisted_options(record.options),
                "status": record.status.value,
                "progress": record.progress,
                "message": record.message,
                "error": sanitize_error_text(record.error) if record.error else None,
                "files": persisted_files,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "owner_user_id": record.owner_user_id,
                "owner_kind": record.owner_kind,
                "license_id": record.license_id,
                "device_id": record.device_id,
                "legacy_unowned": record.legacy_unowned,
                "persistence_version": JOB_PERSISTENCE_VERSION,
                "queue_position": record.queue_position,
                "archived": record.archived,
                "pause_scope": record.pause_scope,
                "runtime_requirements": sorted(record.runtime_requirements),
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

