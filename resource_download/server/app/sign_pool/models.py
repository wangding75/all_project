"""签名池节点模型与 DTO 定义。"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


class NodeConfig(BaseModel):
    """节点配置定义。"""

    id: str
    base_url: str
    labels: list[str] = Field(default_factory=lambda: ["fanqie_sign"])
    capacity: int = 2
    enabled: bool = True


class PoolConfig(BaseModel):
    """节点池配置文件定义。"""

    nodes: list[NodeConfig] = Field(default_factory=list)


@dataclass
class NodeState:
    """节点的内存运行状态（包含容量与租约管理）。"""

    config: NodeConfig
    healthy: bool = True
    fail_count: int = 0
    in_use: int = 0
    last_check: float = 0.0
    leases: dict[str, float] = field(default_factory=dict)  # lease_id -> expire_timestamp

    def clean_expired_leases(self, now: float | None = None) -> int:
        """清理已超期的租约，并更正 in_use 计数。"""
        if now is None:
            now = time.time()
        expired = [lid for lid, exp in self.leases.items() if exp <= now]
        for lid in expired:
            del self.leases[lid]
        if expired:
            self.in_use = max(0, len(self.leases))
        return len(expired)

    def to_dict(self) -> dict[str, Any]:
        """导出为 Ops 诊断的字典结构。"""
        return {
            "id": self.config.id,
            "base_url": self.config.base_url,
            "labels": self.config.labels,
            "capacity": self.config.capacity,
            "enabled": self.config.enabled,
            "healthy": self.healthy,
            "fail_count": self.fail_count,
            "in_use": self.in_use,
            "active_leases": len(self.leases),
            "last_check": self.last_check,
        }


class SignRequest(BaseModel):
    """POST /sign 请求体。"""

    url: str
    headers: dict[str, str] = Field(default_factory=dict)


class SignResponse(BaseModel):
    """POST /sign 响应体（硬约束写死为 {"headers": {...}}）。"""

    headers: dict[str, str] = Field(default_factory=dict)
