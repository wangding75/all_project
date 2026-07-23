"""统一 API DTO。"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PlatformName(str, Enum):
    fanqie = "fanqie"
    hongguo = "hongguo"


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
    cancelled = "cancelled"


class SearchItem(BaseModel):
    id: str
    title: str
    cover: str | None = None
    author: str | None = None
    desc: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class SegmentInfo(BaseModel):
    id: str
    title: str
    index: int = 0
    locked: bool = False


class DetailResponse(BaseModel):
    platform: PlatformName
    id: str
    title: str
    cover: str | None = None
    author: str | None = None
    desc: str | None = None
    segments: list[SegmentInfo] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class JobCreateRequest(BaseModel):
    platform: PlatformName
    id: str
    """书 ID / 剧 ID，或番茄 page URL。"""
    range: str = "all"
    """all | 1-10 | 1,3,5"""
    options: dict[str, Any] = Field(default_factory=dict)


class JobFile(BaseModel):
    file_id: str
    name: str
    size: int = 0
    path: str | None = None


class JobResponse(BaseModel):
    job_id: str
    platform: PlatformName
    item_id: str
    status: JobStatus
    progress: float = 0.0
    message: str = ""
    error: str | None = None
    files: list[JobFile] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    platforms: list[str]


class VersionResponse(BaseModel):
    version: str
    update_check_enabled: bool = False
    latest_version: str
    has_update: bool = False
    download_url: str = ""
    release_notes: str = ""


class RedeemRequest(BaseModel):
    card_code: str


class RedeemResponse(BaseModel):
    success: bool = False
    message: str = "卡密兑换功能暂未开启（Stub）。"
    vip_expires_at: str = ""



class FileItemResponse(BaseModel):
    file_id: str
    title: str
    media_type: str = "video/mp4"
    platform: str = "hongguo"
    size_bytes: int = 0
    size_human: str = "0 B"
    created_at: str = ""


class FileListResponse(BaseModel):
    total: int = 0
    items: list[FileItemResponse] = Field(default_factory=list)


class FileOpenRequest(BaseModel):
    action: str = "play"


class FileOpenResponse(BaseModel):
    success: bool = True
    message: str = ""


class JobsSummaryResponse(BaseModel):
    active_jobs: int = 0
    completed_jobs: int = 0
    total_speed_human: str = "0.0 MB/s"
    disk_free_human: str = "128.4 GB"


class JobListResponse(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: list[JobResponse] = Field(default_factory=list)


