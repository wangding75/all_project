"""统一 API DTO。"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlatformName(str, Enum):
    fanqie = "fanqie"
    hongguo = "hongguo"


class DownloadMode(str, Enum):
    direct = "direct"
    proxy = "proxy"


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


class DownloadResolveRequest(BaseModel):
    """Stable, platform-neutral input for one client download request."""

    platform: PlatformName
    resource_id: str = Field(min_length=1, max_length=512)
    title: str = ""
    media_type: str = "application/octet-stream"
    suggested_filename: str = ""
    range: str = "all"
    options: dict[str, Any] = Field(default_factory=dict, max_length=32)

    @model_validator(mode="after")
    def validate_download_input(self):
        from app.options import split_job_options, validate_range_spec

        split_job_options(self.platform, self.options)
        self.range = validate_range_spec(self.range)
        return self


class DownloadDescriptor(BaseModel):
    """The only download contract exposed to Desktop Client."""

    platform: PlatformName
    resource_id: str
    title: str = ""
    media_type: str = "application/octet-stream"
    suggested_filename: str = "download.bin"
    expires_at: str | None = None
    download_mode: DownloadMode
    url: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    proxy_url: str | None = None
    request_token: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    range_supported: bool | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_transport(self):
        if self.download_mode == DownloadMode.direct and not self.url:
            raise ValueError("direct download descriptor requires url")
        if self.download_mode == DownloadMode.proxy and not self.proxy_url:
            raise ValueError("proxy download descriptor requires proxy_url")
        if self.url and not self.url.startswith(("http://", "https://")):
            raise ValueError("download url must be absolute http(s)")
        return self


class DownloadResolveResponse(BaseModel):
    """Resolve result; ``descriptors`` supports a series/range without changing UI."""

    descriptor: DownloadDescriptor | None = None
    descriptors: list[DownloadDescriptor] = Field(default_factory=list)
    quota: dict[str, Any] = Field(default_factory=dict)
    idempotent_replay: bool = False


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
