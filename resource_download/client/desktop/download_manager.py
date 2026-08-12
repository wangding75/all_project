"""Client-owned queue, concurrency, progress, retry and local history."""

from __future__ import annotations

import queue
import re
import threading
import time
from pathlib import Path
from typing import Any

from .download_models import DownloadDescriptor, DownloadTask, utc_now
from .download_repository import DownloadRepository
from .download_transport import DownloadCancelled, HttpDownloadTransport


def sanitize_filename(value: str, *, fallback: str = "download.bin") -> str:
    clean = Path(str(value or fallback)).name.strip()
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", clean).rstrip(" .")
    return clean or fallback


class DownloadManager:
    def __init__(
        self,
        repository: DownloadRepository,
        download_directory: str | Path,
        *,
        max_concurrent: int = 3,
        transport: HttpDownloadTransport | None = None,
        autostart: bool = True,
    ) -> None:
        self.repository = repository
        self.download_directory = Path(download_directory).expanduser().resolve()
        self.download_directory.mkdir(parents=True, exist_ok=True)
        self.max_concurrent = max(1, int(max_concurrent))
        self.transport = transport or HttpDownloadTransport()
        self._queue: queue.Queue[str] = queue.Queue()
        self._queued: set[str] = set()
        self._cancel: dict[str, threading.Event] = {}
        self._pause: dict[str, threading.Event] = {}
        self._done: dict[str, threading.Event] = {}
        self._lock = threading.RLock()
        self._stopped = False
        self._queue_paused = False
        self._queue_gate = threading.Event()
        self._queue_gate.set()
        self._workers: list[threading.Thread] = []
        self.repository.recover_interrupted()
        if autostart:
            self.start()

    def start(self) -> None:
        with self._lock:
            if self._stopped:
                raise RuntimeError("download manager is shut down")
            while len(self._workers) < self.max_concurrent:
                worker = threading.Thread(target=self._worker, name="rd-download", daemon=True)
                self._workers.append(worker)
                worker.start()
            for task in self.repository.list(statuses=("pending",)):
                self._enqueue_id(task.task_id)

    def shutdown(self, *, wait: bool = True) -> None:
        with self._lock:
            self._stopped = True
            self._queue_gate.set()
            for event in self._cancel.values():
                event.set()
        if wait:
            for worker in self._workers:
                worker.join(timeout=5)
        self.repository.close()

    def _enqueue_id(self, task_id: str) -> None:
        if task_id in self._queued:
            return
        self._queued.add(task_id)
        self._queue.put(task_id)

    def enqueue(self, task_id: str) -> DownloadTask:
        task = self.repository.get(task_id)
        if task is None:
            raise KeyError(task_id)
        with self._lock:
            if task.status not in {"pending", "paused"}:
                raise ValueError(f"cannot enqueue task in state {task.status}")
            task.status = "pending"
            task.error = None
            self.repository.upsert(task)
            self._pause.setdefault(task_id, threading.Event()).clear()
            self._enqueue_id(task_id)
        return task

    def add_descriptor(
        self,
        descriptor: DownloadDescriptor | dict[str, Any],
        *,
        filename: str | None = None,
        subdirectory: str | None = None,
        max_retries: int = 2,
        enqueue: bool = True,
    ) -> DownloadTask:
        if isinstance(descriptor, dict):
            descriptor = DownloadDescriptor.from_mapping(descriptor)
        root = self.download_directory.resolve()
        target_dir = (root / sanitize_filename(subdirectory, fallback="") if subdirectory else root).resolve()
        if not target_dir.is_relative_to(root):
            raise ValueError("download directory escapes client root")
        target_dir.mkdir(parents=True, exist_ok=True)
        preferred = sanitize_filename(filename or descriptor.suggested_filename)
        target = target_dir / preferred
        stem, suffix = target.stem, target.suffix
        index = 1
        while target.exists() or Path(f"{target}.part").exists():
            target = target_dir / f"{stem} ({index}){suffix}"
            index += 1
        task = DownloadTask.new(descriptor, str(target), max_retries=max_retries)
        existing_queue = self.repository.list(statuses=("pending", "paused"))
        task.queue_position = max((item.queue_position for item in existing_queue), default=0) + 1
        self.repository.upsert(task)
        self._cancel[task.task_id] = threading.Event()
        self._pause[task.task_id] = threading.Event()
        self._done[task.task_id] = threading.Event()
        if enqueue:
            self.enqueue(task.task_id)
        return task

    def pause(self, task_id: str) -> DownloadTask:
        task = self._require(task_id)
        with self._lock:
            self._pause.setdefault(task_id, threading.Event()).set()
            if task.status in {"pending", "running"}:
                task.status = "paused"
            elif task.status == "running":
                task.status = "paused"
            self.repository.upsert(task)
        return task

    def resume(self, task_id: str) -> DownloadTask:
        task = self._require(task_id)
        self._pause.setdefault(task_id, threading.Event()).clear()
        if task.status == "paused":
            task.status = "pending"
            self.repository.upsert(task)
            with self._lock:
                self._enqueue_id(task_id)
        return task

    def cancel(self, task_id: str) -> DownloadTask:
        task = self._require(task_id)
        self._cancel.setdefault(task_id, threading.Event()).set()
        task.status = "cancelled"
        task.error = "CLIENT_DOWNLOAD_CANCELLED"
        self.repository.upsert(task)
        self._done.setdefault(task_id, threading.Event()).set()
        return task

    def retry(self, task_id: str) -> DownloadTask:
        task = self._require(task_id)
        if task.status not in {"failed", "cancelled"}:
            raise ValueError(f"cannot retry task in state {task.status}")
        self._cancel[task_id] = threading.Event()
        self._pause[task_id] = threading.Event()
        self._done[task_id] = threading.Event()
        task.status = "pending"
        task.error = None
        task.progress = 0.0 if not Path(task.part_path).exists() else task.progress
        self.repository.upsert(task)
        with self._lock:
            self._enqueue_id(task_id)
        return task

    def pause_queue(self) -> dict[str, Any]:
        with self._lock:
            self._queue_paused = True
            self._queue_gate.clear()
            affected = 0
            for task in self.repository.list(statuses=("pending", "running")):
                self._pause.setdefault(task.task_id, threading.Event()).set()
                task.status = "paused"
                self.repository.upsert(task)
                affected += 1
            return {"paused": True, "affected": affected}

    def resume_queue(self) -> dict[str, Any]:
        with self._lock:
            self._queue_paused = False
            self._queue_gate.set()
            affected = 0
            for task in self.repository.list(statuses=("paused",)):
                self._pause.setdefault(task.task_id, threading.Event()).clear()
                task.status = "pending"
                self.repository.upsert(task)
                self._enqueue_id(task.task_id)
                affected += 1
            return {"paused": False, "affected": affected}

    def reorder(self, task_ids: list[str]) -> dict[str, Any]:
        requested = [str(task_id) for task_id in task_ids]
        affected = 0
        for position, task_id in enumerate(requested, start=1):
            task = self.repository.get(task_id)
            if task is None or task.status not in {"pending", "paused"}:
                continue
            task.queue_position = position
            self.repository.upsert(task)
            affected += 1
        return {"requested": len(requested), "affected": affected}

    def validate_local_files(self) -> dict[str, Any]:
        missing: list[str] = []
        for task in self.repository.list(statuses=("success",)):
            if not Path(task.local_path).is_file():
                task.status = "failed"
                task.error = "LOCAL_FILE_MISSING"
                self.repository.upsert(task)
                missing.append(task.task_id)
        return {"checked": len(self.repository.list()), "missing": missing}

    def wait_for(self, task_id: str, timeout: float = 30.0) -> DownloadTask | None:
        task = self._require(task_id)
        event = self._done.setdefault(task_id, threading.Event())
        event.wait(timeout=max(0.0, float(timeout)))
        return self.repository.get(task_id)

    def list_tasks(self) -> list[DownloadTask]:
        return self.repository.list()

    def history(self) -> list[DownloadTask]:
        return self.repository.history()

    def local_files(self) -> list[dict[str, Any]]:
        return self.repository.file_index(existing_only=False)

    def summary(self) -> dict[str, Any]:
        tasks = self.repository.list()
        active = sum(task.status in {"pending", "running", "paused"} for task in tasks)
        completed = sum(task.status == "success" for task in tasks)
        return {
            "active_jobs": active,
            "completed_jobs": completed,
            "total_speed_human": "0 B/s",
            "disk_free_human": "unknown",
        }

    def queue_state(self) -> dict[str, Any]:
        tasks = self.repository.list()
        pending = [task for task in tasks if task.status in {"pending", "paused"}]
        running = sum(task.status == "running" for task in tasks)
        return {
            "paused": self._queue_paused,
            "max_concurrent_jobs": self.max_concurrent,
            "running_count": running,
            "pending_count": len(pending),
            "items": [self.as_job(task) for task in pending],
        }

    @staticmethod
    def as_job(task: DownloadTask) -> dict[str, Any]:
        path = Path(task.local_path)
        files = []
        if task.status == "success":
            files.append(
                {
                    "file_id": task.task_id,
                    "name": path.name,
                    "size": path.stat().st_size if path.is_file() else task.total_bytes,
                    "path": str(path),
                    "local_path": str(path),
                }
            )
        return {
            "job_id": task.task_id,
            "platform": task.descriptor.platform,
            "item_id": task.descriptor.resource_id,
            "status": task.status,
            "progress": task.progress,
            "message": task.error or "",
            "error": task.error,
            "files": files,
            "extra": {
                "title": task.descriptor.title,
                "queue_position": 0,
                "local_path": task.local_path,
                "downloaded_bytes": task.downloaded_bytes,
                "total_bytes": task.total_bytes,
                "retry_count": task.retry_count,
                "queue_position": task.queue_position,
            },
        }

    def _require(self, task_id: str) -> DownloadTask:
        task = self.repository.get(task_id)
        if task is None:
            raise KeyError(task_id)
        return task

    def _worker(self) -> None:
        while True:
            if self._stopped and self._queue.empty():
                return
            if not self._queue_gate.wait(timeout=0.2):
                continue
            try:
                task_id = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            with self._lock:
                self._queued.discard(task_id)
            try:
                self._run_task(task_id)
            finally:
                self._queue.task_done()

    def _run_task(self, task_id: str) -> None:
        task = self.repository.get(task_id)
        if task is None or task.status in {"cancelled", "success"}:
            return
        pause_event = self._pause.setdefault(task_id, threading.Event())
        cancel_event = self._cancel.setdefault(task_id, threading.Event())
        if pause_event.is_set():
            task.status = "paused"
            self.repository.upsert(task)
            return
        task.status = "running"
        task.started_at = task.started_at or utc_now()
        task.error = None
        self.repository.upsert(task)

        url = task.descriptor.url if task.descriptor.download_mode == "direct" else task.descriptor.proxy_url
        if not url or not str(url).startswith(("http://", "https://")):
            self._finish_error(task, "DOWNLOAD_DESCRIPTOR_URL_INVALID")
            return
        part = Path(task.part_path)
        try:
            downloaded, total, _range_used = self.transport.download(
                str(url),
                part,
                headers=task.descriptor.headers,
                expected_size=task.descriptor.size_bytes,
                range_supported=task.descriptor.range_supported,
                progress=lambda done, size: self._progress(task_id, done, size),
                cancel_event=cancel_event,
                pause_event=pause_event,
            )
            if cancel_event.is_set():
                raise DownloadCancelled("CLIENT_DOWNLOAD_CANCELLED")
            if pause_event.is_set():
                task.status = "paused"
                task.downloaded_bytes = downloaded
                task.total_bytes = total
                task.progress = (downloaded / total * 100.0) if total else task.progress
                self.repository.upsert(task)
                return
            Path(task.part_path).replace(task.local_path)
            task.status = "success"
            task.downloaded_bytes = downloaded
            task.total_bytes = total
            task.progress = 100.0
            task.completed_at = utc_now()
            task.error = None
            self.repository.upsert(task)
            self._done.setdefault(task_id, threading.Event()).set()
        except DownloadCancelled:
            task.status = "cancelled"
            task.error = "CLIENT_DOWNLOAD_CANCELLED"
            self.repository.upsert(task)
            self._done.setdefault(task_id, threading.Event()).set()
        except Exception as exc:  # noqa: BLE001
            if task.retry_count < task.max_retries and not self._stopped and not cancel_event.is_set():
                task.retry_count += 1
                task.status = "pending"
                task.error = type(exc).__name__
                self.repository.upsert(task)
                time.sleep(min(2.0, 0.2 * task.retry_count))
                with self._lock:
                    self._enqueue_id(task_id)
            else:
                self._finish_error(task, type(exc).__name__)

    def _progress(self, task_id: str, downloaded: int, total: int) -> None:
        task = self.repository.get(task_id)
        if task is None or task.status == "cancelled":
            return
        task.downloaded_bytes = int(downloaded)
        task.total_bytes = int(total)
        task.progress = min(100.0, downloaded / total * 100.0) if total else task.progress
        self.repository.upsert(task)

    def _finish_error(self, task: DownloadTask, message: str) -> None:
        task.status = "failed"
        task.error = message
        self.repository.upsert(task)
        self._done.setdefault(task.task_id, threading.Event()).set()
