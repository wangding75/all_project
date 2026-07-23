"""结构化日志与运行指标统计器 (Stage E5)。"""

from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger("app.structured")


def log_context(
    level: int,
    message: str,
    job_id: str | None = None,
    user_id: int | None = None,
    platform: str | None = None,
    error_code: str | None = None,
    extra_data: dict[str, Any] | None = None,
) -> None:
    """输出包含结构化上下文信息的标准日志。"""
    ctx_parts = []
    if user_id is not None:
        ctx_parts.append(f"user_id={user_id}")
    if job_id:
        ctx_parts.append(f"job_id={job_id}")
    if platform:
        ctx_parts.append(f"platform={platform}")
    if error_code:
        ctx_parts.append(f"error_code={error_code}")

    ctx_str = f"[{' '.join(ctx_parts)}] " if ctx_parts else ""
    extra_str = f" extra={extra_data}" if extra_data else ""
    logger.log(level, f"{ctx_str}{message}{extra_str}")


class MetricsTracker:
    """进程内轻量级运行指标统计器。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.total_requests: int = 0
        self.jobs_created_count: int = 0
        self.jobs_success_count: int = 0
        self.jobs_failed_count: int = 0
        self.platform_stats: dict[str, dict[str, int]] = {
            "fanqie": {"created": 0, "success": 0, "failed": 0},
            "hongguo": {"created": 0, "success": 0, "failed": 0},
        }

    def inc_request(self) -> None:
        with self._lock:
            self.total_requests += 1

    def record_job_created(self, platform: str) -> None:
        with self._lock:
            self.jobs_created_count += 1
            if platform in self.platform_stats:
                self.platform_stats[platform]["created"] += 1

    def record_job_success(self, platform: str) -> None:
        with self._lock:
            self.jobs_success_count += 1
            if platform in self.platform_stats:
                self.platform_stats[platform]["success"] += 1

    def record_job_failed(self, platform: str) -> None:
        with self._lock:
            self.jobs_failed_count += 1
            if platform in self.platform_stats:
                self.platform_stats[platform]["failed"] += 1

    def get_summary(self) -> dict[str, Any]:
        with self._lock:
            return {
                "total_requests": self.total_requests,
                "jobs_created_count": self.jobs_created_count,
                "jobs_success_count": self.jobs_success_count,
                "jobs_failed_count": self.jobs_failed_count,
                "platform_stats": {
                    k: dict(v) for k, v in self.platform_stats.items()
                },
            }


# 单例运行指标统计对象
metrics_tracker = MetricsTracker()
