"""统一 API DTO。"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class PlatformName(str, Enum):
    fanqie = "fanqie"
    hongguo = "hongguo"


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    cancelling = "cancelling"
    success = "success"
    failed = "failed"
    cancelled = "cancelled"


class SearchItem(BaseModel):
    id: str
    title: str
    cover: str | None = None
    author: str | None = None
    desc: str | None = None
    # 来源平台（聚合搜索时必填；单平台搜索也会回填）
    platform: PlatformName | None = None
    # 人类可读来源标记，如「番茄小说」「红果短剧」
    source_label: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """聚合/单平台搜索统一响应。"""

    items: list[SearchItem] = Field(default_factory=list)
    platforms_queried: list[str] = Field(default_factory=list)
    # 某平台失败时仍返回其它平台结果，错误写在此
    platform_errors: dict[str, str] = Field(default_factory=dict)
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_more: bool = False


class DiscoverItem(BaseModel):
    """首页热榜 / 上新条目（数据来自服务端聚合，客户端只展示）。"""

    rank: int | None = None
    id: str
    title: str
    cover: str | None = None
    author: str | None = None
    desc: str | None = None
    platform: PlatformName
    source_label: str | None = None
    badge: str | None = None  # 热 / 新 / 飙升 等
    extra: dict[str, Any] = Field(default_factory=dict)


class DiscoverSection(BaseModel):
    kind: str  # hot | new
    title: str
    items: list[DiscoverItem] = Field(default_factory=list)
    available: bool = False
    message: str = ""
    platform_errors: dict[str, str] = Field(default_factory=dict)


class DiscoverResponse(BaseModel):
    sections: list[DiscoverSection] = Field(default_factory=list)
    platforms_queried: list[str] = Field(default_factory=list)
    # live | unavailable
    data_mode: str = "unavailable"
    note: str = ""


class BatchJobItem(BaseModel):
    platform: PlatformName
    id: str = Field(min_length=1)
    range: str = "all"
    options: dict[str, Any] = Field(default_factory=dict)


class BatchJobCreateRequest(BaseModel):
    items: list[BatchJobItem] = Field(min_length=1, max_length=100)
    queue_mode: Literal["enqueue", "start_immediately"] = "enqueue"
    duplicate_policy: Literal["skip_completed", "retry_failed", "create_anyway"] = (
        "skip_completed"
    )


class BatchJobCreatedItem(BaseModel):
    item_id: str
    platform: PlatformName
    job_id: str


class BatchJobSkippedItem(BaseModel):
    item_id: str
    platform: PlatformName
    reason: str
    existing_job_id: str | None = None


class BatchJobErrorItem(BaseModel):
    item_id: str
    platform: PlatformName
    message: str


class BatchJobCreateResponse(BaseModel):
    batch_id: str
    created: list[BatchJobCreatedItem] = Field(default_factory=list)
    skipped: list[BatchJobSkippedItem] = Field(default_factory=list)
    errors: list[BatchJobErrorItem] = Field(default_factory=list)


class BatchResolveRequest(BaseModel):
    inputs: list[str] = Field(min_length=1, max_length=100)
    platform_hint: Literal["all", "hongguo", "fanqie"] = "all"


class BatchResolvedItem(BaseModel):
    input: str
    resolved: bool = True
    content: SearchItem


class BatchResolveErrorItem(BaseModel):
    input: str
    code: str
    message: str


class BatchResolveResponse(BaseModel):
    items: list[BatchResolvedItem] = Field(default_factory=list)
    errors: list[BatchResolveErrorItem] = Field(default_factory=list)


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


class HealthDependencyItem(BaseModel):
    """单项依赖检查结果，供 UI 列表展示。"""

    key: str
    label: str
    ok: bool = False
    required: bool = True
    message: str = ""
    hints: list[str] = Field(default_factory=list)
    detail: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str = "ok"  # ok | degraded | error
    version: str
    platforms: list[str]
    # 运行时依赖（番茄签名/书名搜索等）；缺失时 status 可为 degraded
    dependencies: dict[str, Any] = Field(default_factory=dict)
    # 扁平列表，方便 UI 直接渲染
    checks: list[HealthDependencyItem] = Field(default_factory=list)
    # 人类可读摘要
    summary: str = ""


class VersionResponse(BaseModel):
    version: str
    update_check_enabled: bool = False
    latest_version: str
    has_update: bool = False
    download_url: str = ""
    sha256: str = ""
    mandatory: bool = False
    minimum_supported_version: str = ""
    rollout_percentage: int = 100
    release_notes: str = ""


class RedeemRequest(BaseModel):
    card_code: str


class RedeemResponse(BaseModel):
    success: bool = False
    message: str = ""
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
    total_speed_human: str = "0 B/s"
    disk_free_human: str = "128.4 GB"


class JobListResponse(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: list[JobResponse] = Field(default_factory=list)


