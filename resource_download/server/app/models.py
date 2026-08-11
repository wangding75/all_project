"""统一 API DTO。"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlatformName(str, Enum):
    fanqie = "fanqie"
    hongguo = "hongguo"


class JobStatus(str, Enum):
    pending = "pending"
    paused = "paused"
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
    # Explicit outcome codes let the UI distinguish empty from runtime/upstream failure.
    platform_status: dict[str, str] = Field(default_factory=dict)
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
    options: dict[str, Any] = Field(default_factory=dict, max_length=32)

    @model_validator(mode="after")
    def validate_download_input(self):
        from app.options import split_job_options, validate_range_spec

        split_job_options(self.platform, self.options)
        self.range = validate_range_spec(self.range)
        return self


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


class ImageRecognizeRequest(BaseModel):
    image_base64: str = Field(min_length=16, max_length=12 * 1024 * 1024)
    platform_hint: Literal["all", "hongguo", "fanqie"] = "all"
    max_candidates: int = Field(default=5, ge=1, le=10)


class ImageRecognizeCandidate(BaseModel):
    score: float = Field(ge=0, le=1)
    confidence: Literal["high", "medium", "low"]
    method: str = "cover_similarity"
    content: DiscoverItem


class ImageRecognizeResponse(BaseModel):
    candidates: list[ImageRecognizeCandidate] = Field(default_factory=list)
    compared_count: int = 0
    platform_errors: dict[str, str] = Field(default_factory=dict)


class PersonWork(BaseModel):
    id: str
    title: str
    cover: str | None = None
    role: str = ""
    episode_count: int = 0


class PersonProfile(BaseModel):
    name: str
    avatar: str | None = None
    intro: str = ""
    works: list[PersonWork] = Field(default_factory=list)


class PeopleResponse(BaseModel):
    people: list[PersonProfile] = Field(default_factory=list)
    scanned_works: int = 0
    errors: list[str] = Field(default_factory=list)


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
    options: dict[str, Any] = Field(default_factory=dict, max_length=32)

    @model_validator(mode="after")
    def validate_download_input(self):
        from app.options import split_job_options, validate_range_spec

        split_job_options(self.platform, self.options)
        self.range = validate_range_spec(self.range)
        return self


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


class DeviceProofRequest(BaseModel):
    """LS-DEVICE-V3 proof fields transported by the RD API."""

    timestamp: int | None = None
    nonce: str | None = None
    signature: str | None = None


class RedeemRequest(BaseModel):
    """Activation proxy request.

    ``card_code`` is kept as the external compatibility name.  It is passed to
    License Service as ``license_key`` and is never looked up in RD SQLite.
    """

    card_code: str
    device_id: str | None = None
    device_key_algorithm: str | None = None
    device_public_key: str | None = None
    proof: DeviceProofRequest | None = None


class RedeemResponse(BaseModel):
    success: bool = False
    message: str = ""
    reason: str = ""
    license_expires_at: str | None = None
    max_devices: int | None = None
    active_devices: int | None = None
    license_id: str | None = None
    device_id: str | None = None
    plan_code: str | None = None
    plan_version: int | None = None
    entitlement_schema_version: int | None = None
    entitlements: dict[str, Any] = Field(default_factory=dict)
    # Deprecated display alias. It is not an authorization fact and is never
    # persisted back to User.vip_expires_at by the new activation flow.
    vip_expires_at: str | None = None



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


class QueueStateResponse(BaseModel):
    paused: bool = False
    max_concurrent_jobs: int = 1
    running_count: int = 0
    pending_count: int = 0
    items: list[JobResponse] = Field(default_factory=list)


class QueueReorderRequest(BaseModel):
    job_ids: list[str] = Field(min_length=1, max_length=100)


class QueueBulkRequest(BaseModel):
    job_ids: list[str] = Field(min_length=1, max_length=100)


class QueueBulkActionRequest(QueueBulkRequest):
    action: Literal["pause", "resume", "cancel", "archive"]


class QueueBulkResponse(BaseModel):
    action: str
    requested: int = 0
    affected: int = 0
    skipped: list[str] = Field(default_factory=list)


class HongguoMonitorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    auto_enqueue: bool = False
    interval_seconds: int = Field(default=60, ge=30, le=86400)
    scan_limit: int = Field(default=50, ge=1, le=50)
    min_episode_count: int = Field(default=0, ge=0, le=10000)
    max_auto_enqueue_per_scan: int = Field(default=20, ge=1, le=50)
    include_keywords: list[str] = Field(default_factory=list, max_length=20)
    exclude_keywords: list[str] = Field(default_factory=list, max_length=20)
    author_keywords: list[str] = Field(default_factory=list, max_length=20)
    quality: str = "1080p"
    concurrency: int = Field(default=2, ge=1, le=12)
    download_cover: bool = False
    download_desc: bool = False


class HongguoMonitorLog(BaseModel):
    timestamp: str
    level: Literal["info", "warning", "error"] = "info"
    message: str
    detected: int = 0
    enqueued: int = 0


class HongguoMonitorStatus(HongguoMonitorConfig):
    license_context_status: Literal["READY", "REAUTH_REQUIRED"] = "REAUTH_REQUIRED"
    baseline_initialized: bool = False
    known_count: int = 0
    last_scan_at: str = ""
    last_success_at: str = ""
    last_error: str = ""
    last_detected_count: int = 0
    total_detected_count: int = 0
    total_enqueued_count: int = 0
    next_scan_at: str = ""
    recent_items: list[DiscoverItem] = Field(default_factory=list)
    logs: list[HongguoMonitorLog] = Field(default_factory=list)


