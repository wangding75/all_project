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
