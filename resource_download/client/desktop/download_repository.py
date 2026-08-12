"""SQLite persistence owned by Desktop Client."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable

from .download_models import DownloadTask


SCHEMA_VERSION = 1


class DownloadRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).expanduser().resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(str(self.database_path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        with self._lock, self._connection:
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )
            self._connection.execute(
                """CREATE TABLE IF NOT EXISTS download_tasks (
                    task_id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    media_type TEXT NOT NULL DEFAULT 'application/octet-stream',
                    suggested_filename TEXT NOT NULL DEFAULT 'download.bin',
                    expires_at TEXT,
                    download_mode TEXT NOT NULL,
                    url TEXT,
                    headers_json TEXT NOT NULL DEFAULT '{}',
                    proxy_url TEXT,
                    request_token TEXT,
                    size_bytes INTEGER,
                    range_supported INTEGER,
                    extra_json TEXT NOT NULL DEFAULT '{}',
                    local_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL DEFAULT 0,
                    total_bytes INTEGER NOT NULL DEFAULT 0,
                    downloaded_bytes INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 2,
                    error TEXT
                )"""
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_download_tasks_status_created "
                "ON download_tasks(status, created_at)"
            )
            self._connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)",
                (SCHEMA_VERSION,),
            )

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def upsert(self, task: DownloadTask) -> None:
        record = task.to_record()
        columns = list(record)
        placeholders = ", ".join("?" for _ in columns)
        updates = ", ".join(f"{column}=excluded.{column}" for column in columns if column != "task_id")
        with self._lock, self._connection:
            self._connection.execute(
                f"INSERT INTO download_tasks ({', '.join(columns)}) VALUES ({placeholders}) "
                f"ON CONFLICT(task_id) DO UPDATE SET {updates}",
                [record[column] for column in columns],
            )

    def update(self, task: DownloadTask, **fields: Any) -> DownloadTask:
        for key, value in fields.items():
            if not hasattr(task, key):
                raise AttributeError(f"unknown download task field: {key}")
            setattr(task, key, value)
        self.upsert(task)
        return task

    def get(self, task_id: str) -> DownloadTask | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM download_tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
        return DownloadTask.from_record(dict(row)) if row else None

    def list(self, *, statuses: Iterable[str] | None = None) -> list[DownloadTask]:
        values = list(statuses or [])
        query = "SELECT * FROM download_tasks"
        params: list[Any] = []
        if values:
            query += f" WHERE status IN ({', '.join('?' for _ in values)})"
            params.extend(values)
        query += " ORDER BY created_at ASC, task_id ASC"
        with self._lock:
            rows = self._connection.execute(query, params).fetchall()
        return [DownloadTask.from_record(dict(row)) for row in rows]

    def history(self) -> list[DownloadTask]:
        return self.list(statuses=("success", "failed", "cancelled"))

    def recover_interrupted(self) -> list[DownloadTask]:
        tasks = self.list(statuses=("running",))
        for task in tasks:
            task.status = "pending"
            task.error = "CLIENT_RESTART_RECOVERY"
            self.upsert(task)
        return tasks

    def remove(self, task_id: str) -> None:
        with self._lock, self._connection:
            self._connection.execute("DELETE FROM download_tasks WHERE task_id = ?", (task_id,))

    def file_index(self, *, existing_only: bool = False) -> list[dict[str, Any]]:
        tasks = self.list(statuses=("success",))
        result: list[dict[str, Any]] = []
        for task in tasks:
            path = Path(task.local_path)
            exists = path.is_file()
            if existing_only and not exists:
                continue
            result.append(
                {
                    "file_id": task.task_id,
                    "task_id": task.task_id,
                    "title": task.title or task.descriptor.title or path.name,
                    "name": path.name,
                    "path": str(path),
                    "local_path": str(path),
                    "media_type": task.descriptor.media_type,
                    "platform": task.descriptor.platform,
                    "size_bytes": path.stat().st_size if exists else task.total_bytes,
                    "exists": exists,
                    "created_at": task.completed_at or task.created_at,
                }
            )
        return result
