"""基于 IP 的请求频率限制器（进程内内存固定窗口）。"""

from __future__ import annotations

import logging
import time
from threading import Lock
from fastapi import Depends, HTTPException, Request, status

from app.config import get_settings

logger = logging.getLogger(__name__)

# 全局限流缓存锁与存储
# 结构: { f"{bucket}:{ip}:{minute}": count }
_rate_limit_lock = Lock()
_rate_limit_cache: dict[str, int] = {}


def check_rate_limit(request: Request, limit: int, bucket: str = "global") -> None:
    """通用请求频率检查逻辑。"""
    if limit <= 0:
        return

    path = request.url.path

    # 1. 探活与根路径免限流
    if path == "/health" or path == "/":
        return

    # 2. 全局限流排他，避免对注册/登录双计
    if bucket == "global":
        if "/v1/auth/register" in path or "/v1/auth/login" in path:
            return

    # 3. 获取客户端 IP
    ip = request.client.host if request.client else "unknown"

    current_minute = int(time.time()) // 60
    key = f"{bucket}:{ip}:{current_minute}"

    with _rate_limit_lock:
        # 缓存垃圾清理：仅保留近 2 分钟内的键，防止内存泄漏
        keys_to_del = []
        for cached_key in _rate_limit_cache:
            try:
                parts = cached_key.split(":")
                minute_val = int(parts[-1])
                if current_minute - minute_val > 2:
                    keys_to_del.append(cached_key)
            except (ValueError, IndexError):
                pass
        for cached_key in keys_to_del:
            _rate_limit_cache.pop(cached_key, None)

        # 计数校验
        count = _rate_limit_cache.get(key, 0)
        if count >= limit:
            logger.warning(
                "IP %s exceeded %s limit (%d/min) on path %s",
                ip,
                bucket,
                limit,
                path,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁",
                headers={"Retry-After": "60"},
            )

        _rate_limit_cache[key] = count + 1


def ip_rate_limiter(kind: str = "global"):
    """FastAPI 依赖项生成器。"""
    async def dependency(request: Request) -> None:
        settings = get_settings()
        if kind == "auth":
            limit = settings.rate_limit_auth_per_minute
            check_rate_limit(request, limit, bucket="auth")
        else:
            limit = settings.rate_limit_per_minute
            check_rate_limit(request, limit, bucket="global")

    return dependency
