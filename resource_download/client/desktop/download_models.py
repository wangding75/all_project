"""Client-owned download data contracts."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


DownloadStatus = Literal["pending", "running", "paused", "success", "failed", "cancelled"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DownloadDescriptor:
    platform: str
    resource_id: str
    title: str = ""
    media_type: str = "application/octet-stream"
    suggested_filename: str = "download.bin"
    expires_at: str | None = None
    download_mode: Literal["direct", "proxy"] = "direct"
    url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    proxy_url: str | None = None
    request_token: str | None = None
    size_bytes: int | None = None
    range_supported: bool | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "DownloadDescriptor":
        data = dict(payload)
        data["platform"] = str(data.get("platform") or "")
        data["resource_id"] = str(data.get("resource_id") or "")
        data["download_mode"] = str(data.get("download_mode") or "direct")
        data["headers"] = {str(k): str(v) for k, v in dict(data.get("headers") or {}).items()}
        data["extra"] = dict(data.get("extra") or {})
        return cls(**{key: data[key] for key in cls.__dataclass_fields__ if key in data})

    def to_mapping(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "resource_id": self.resource_id,
            "title": self.title,
            "media_type": self.media_type,
            "suggested_filename": self.suggested_filename,
            "expires_at": self.expires_at,
            "download_mode": self.download_mode,
            "url": self.url,
            "headers": dict(self.headers),
            "proxy_url": self.proxy_url,
            "request_token": self.request_token,
            "size_bytes": self.size_bytes,
            "range_supported": self.range_supported,
            "extra": dict(self.extra),
        }


@dataclass
class DownloadTask:
    task_id: str
    descriptor: DownloadDescriptor
    local_path: str
    status: DownloadStatus = "pending"
    progress: float = 0.0
    total_bytes: int = 0
    downloaded_bytes: int = 0
    created_at: str = field(default_factory=utc_now)
    started_at: str | None = None
    completed_at: str | None = None
    retry_count: int = 0
    max_retries: int = 2
    error: str | None = None

    @classmethod
    def new(
        cls,
        descriptor: DownloadDescriptor,
        local_path: str,
        *,
        task_id: str | None = None,
        max_retries: int = 2,
    ) -> "DownloadTask":
        return cls(
            task_id=task_id or f"dl_{uuid.uuid4().hex}",
            descriptor=descriptor,
            local_path=local_path,
            max_retries=max(0, int(max_retries)),
        )

    @property
    def part_path(self) -> str:
        return f"{self.local_path}.part"

    def to_record(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "platform": self.descriptor.platform,
            "resource_id": self.descriptor.resource_id,
            "title": self.descriptor.title,
            "media_type": self.descriptor.media_type,
            "suggested_filename": self.descriptor.suggested_filename,
            "expires_at": self.descriptor.expires_at,
            "download_mode": self.descriptor.download_mode,
            "url": self.descriptor.url,
            "headers_json": json.dumps(self.descriptor.headers, ensure_ascii=False, sort_keys=True),
            "proxy_url": self.descriptor.proxy_url,
            "request_token": self.descriptor.request_token,
            "size_bytes": self.descriptor.size_bytes,
            "range_supported": self.descriptor.range_supported,
            "extra_json": json.dumps(self.descriptor.extra, ensure_ascii=False, sort_keys=True),
            "local_path": self.local_path,
            "status": self.status,
            "progress": self.progress,
            "total_bytes": self.total_bytes,
            "downloaded_bytes": self.downloaded_bytes,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error": self.error,
        }

    @classmethod
    def from_record(cls, row: dict[str, Any]) -> "DownloadTask":
        descriptor = DownloadDescriptor(
            platform=str(row.get("platform") or ""),
            resource_id=str(row.get("resource_id") or ""),
            title=str(row.get("title") or ""),
            media_type=str(row.get("media_type") or "application/octet-stream"),
            suggested_filename=str(row.get("suggested_filename") or "download.bin"),
            expires_at=row.get("expires_at"),
            download_mode=str(row.get("download_mode") or "direct"),
            url=row.get("url"),
            headers=json.loads(row.get("headers_json") or "{}"),
            proxy_url=row.get("proxy_url"),
            request_token=row.get("request_token"),
            size_bytes=row.get("size_bytes"),
            range_supported=bool(row["range_supported"]) if row.get("range_supported") is not None else None,
            extra=json.loads(row.get("extra_json") or "{}"),
        )
        return cls(
            task_id=str(row["task_id"]),
            descriptor=descriptor,
            local_path=str(row["local_path"]),
            status=str(row.get("status") or "pending"),
            progress=float(row.get("progress") or 0.0),
            total_bytes=int(row.get("total_bytes") or 0),
            downloaded_bytes=int(row.get("downloaded_bytes") or 0),
            created_at=str(row.get("created_at") or utc_now()),
            started_at=row.get("started_at"),
            completed_at=row.get("completed_at"),
            retry_count=int(row.get("retry_count") or 0),
            max_retries=int(row.get("max_retries") or 0),
            error=row.get("error"),
        )
