"""签名节点池包（单例导出与常用方法）。"""

from __future__ import annotations

import threading

from app.config import get_settings
from app.sign_pool.client import sign_via_pool
from app.sign_pool.errors import SignPoolError, SignPoolUnavailableError
from app.sign_pool.pool import SignPool

_pool_instance: SignPool | None = None
_pool_lock = threading.Lock()


def get_sign_pool() -> SignPool:
    """获取进程内单例 SignPool 对象。"""
    global _pool_instance
    if _pool_instance is None:
        with _pool_lock:
            if _pool_instance is None:
                pool = SignPool()
                settings = get_settings()
                pool.load_from_config(
                    config_path=settings.sign_pool_config_path,
                    urls=settings.sign_pool_urls,
                )
                _pool_instance = pool
    return _pool_instance


def reset_sign_pool() -> None:
    """重置单例对象（主要用于 pytest 测试用例隔离）。"""
    global _pool_instance
    with _pool_lock:
        _pool_instance = None


__all__ = [
    "SignPool",
    "SignPoolError",
    "SignPoolUnavailableError",
    "get_sign_pool",
    "reset_sign_pool",
    "sign_via_pool",
]
