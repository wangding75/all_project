"""管理员与运维 DTO 架构。"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class UserStatusUpdateRequest(BaseModel):
    """设置用户启用/禁用状态。"""

    is_active: bool = Field(..., description="是否启用账号")


class UserStatusUpdateResponse(BaseModel):
    """更新用户状态响应。"""

    id: int
    username: str
    is_active: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchInvalidateRequest(BaseModel):
    """按 batch_id 作废卡密请求。"""

    batch_id: str = Field(..., min_length=1, description="需作废的卡密批次 ID")


class BatchInvalidateResponse(BaseModel):
    """作废卡密响应。"""

    batch_id: str
    invalidated_count: int = Field(..., description="成功作废的卡密数量")


class UserDetailResponse(BaseModel):
    """运维查询用户详细状态。"""

    id: int
    username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    vip_expires_at: datetime | None = Field(
        default=None,
        description="DEPRECATED legacy display field; not License authorization",
    )
    is_vip: bool
    job_count_today: int = 0

    model_config = ConfigDict(from_attributes=True)


class UserListItem(BaseModel):
    """用户列表项。"""

    id: int
    username: str
    is_active: bool
    created_at: datetime
    vip_expires_at: datetime | None = Field(
        default=None,
        description="DEPRECATED legacy display field; not License authorization",
    )
    is_vip: bool

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """用户列表响应。"""

    total: int
    users: list[UserListItem]


class AdminHealthResponse(BaseModel):
    """运维管理员健康探活响应。"""

    status: str = "ok"
    db_status: str = "ok"
    disk_free_human: str = "0 B"
    disk_free_bytes: int = 0
    active_jobs: int = 0
    sign_pool_summary: dict[str, Any] = Field(default_factory=dict)
    license_service_configured: bool = False
    license_service_reachable: bool = False
    license_cache_ttl_seconds: int = 0


class AdminMetricsResponse(BaseModel):
    """运维运行指标数据响应。"""

    total_requests: int = 0
    jobs_created_count: int = 0
    jobs_success_count: int = 0
    jobs_failed_count: int = 0
    platform_stats: dict[str, dict[str, int]] = Field(default_factory=dict)
