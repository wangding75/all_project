"""进程内任务队列（MVP-1）。"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings
from app.models import JobFile, JobResponse, JobStatus, PlatformName
from platforms.registry import get_platform


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

    def to_response(self) -> JobResponse:
        return JobResponse(
            job_id=self.job_id,
            platform=self.platform,
            item_id=self.item_id,
            status=self.status,
            progress=self.progress,
            message=self.message,
            error=self.error,
            files=list(self.files),
            extra={"created_at": self.created_at, "updated_at": self.updated_at},
        )


class JobManager:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.settings.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.settings.outputs_dir.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, JobRecord] = {}
        self._lock = asyncio.Lock()

    async def create_job(
        self,
        platform: PlatformName,
        item_id: str,
        range_spec: str = "all",
        options: dict[str, Any] | None = None,
    ) -> JobRecord:
        job_id = uuid.uuid4().hex[:12]
        record = JobRecord(
            job_id=job_id,
            platform=platform,
            item_id=item_id,
            range_spec=range_spec or "all",
            options=options or {},
        )
        async with self._lock:
            self._jobs[job_id] = record
        self._persist(record)
        asyncio.create_task(self._run_job(job_id))
        return record

    async def get_job(self, job_id: str) -> JobRecord | None:
        async with self._lock:
            return self._jobs.get(job_id)

    def resolve_file(self, file_id: str) -> Path | None:
        for record in self._jobs.values():
            for f in record.files:
                if f.file_id == file_id:
                    path = Path(f.path) if f.path else None
                    if path and path.is_file():
                        return path
        # 路径安全校验：防止路径穿越攻击
        outputs_root = self.settings.outputs_dir.resolve()
        candidate = (outputs_root / file_id).resolve()
        if not candidate.is_relative_to(outputs_root):
            return None
        if candidate.is_file():
            return candidate
        return None

    async def _run_job(self, job_id: str) -> None:
        async with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return
            record.status = JobStatus.running
            record.message = "running"
            record.updated_at = _utc_now()
        self._persist(record)

        out_dir = self.settings.outputs_dir / job_id
        out_dir.mkdir(parents=True, exist_ok=True)

        def on_progress(pct: float, msg: str) -> None:
            record.progress = max(0.0, min(100.0, float(pct)))
            record.message = msg
            record.updated_at = _utc_now()

        try:
            platform = get_platform(record.platform)

            def progress_cb(pct: float, msg: str) -> None:
                on_progress(pct, msg)

            paths = await platform.download(
                record.item_id,
                out_dir,
                range_spec=record.range_spec,
                options=record.options,
                progress=progress_cb,
            )
            files: list[JobFile] = []
            for path in paths:
                path = Path(path)
                rel = f"{job_id}/{path.name}"
                # 若文件在子目录，保留相对 outputs 的路径
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
                record.status = JobStatus.success
                record.progress = 100.0
                record.message = "success"
                record.files = files
                record.error = None
                record.updated_at = _utc_now()
            self._persist(record)
        except Exception as exc:  # noqa: BLE001 — 任务边界捕获
            async with self._lock:
                record.status = JobStatus.failed
                record.error = str(exc)
                record.message = "failed"
                record.updated_at = _utc_now()
            self._persist(record)

    def _persist(self, record: JobRecord) -> None:
        path = self.settings.jobs_dir / f"{record.job_id}.json"
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
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


_manager: JobManager | None = None


def get_job_manager() -> JobManager:
    global _manager
    if _manager is None:
        _manager = JobManager()
    return _manager
