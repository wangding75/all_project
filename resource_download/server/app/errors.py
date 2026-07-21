"""服务端与平台层统一错误映射工具（阶段 E0）。

将裸 Exception / Traceback 字符串归类映射为人类可读、规范化的错误提示。
"""

from __future__ import annotations

import logging

from app.sign_pool.errors import SignPoolError, SignPoolUnavailableError

logger = logging.getLogger(__name__)


def format_platform_error(exc: Exception) -> str:
    """将平台捕获的各种异常归类为人类可读且可归类的短语。"""
    if isinstance(exc, SignPoolUnavailableError):
        return exc.message
    if isinstance(exc, SignPoolError):
        return "签名节点繁忙或不可用，请稍后重试"

    exc_str = str(exc)
    exc_lower = exc_str.lower()

    # 1. 签名池 503 匹配
    if "签名节点" in exc_str or "signpool" in exc_lower:
        return "签名节点繁忙或不可用，请稍后重试"

    # 2. Vendor 缺失
    if "hongguovendorerror" in exc_lower or "missing vendor" in exc_lower:
        return f"红果 Vendor 组件未处于就绪状态: {exc_str}"

    # 3. 会话 / 鉴权 / Cookie 失效
    if any(k in exc_lower for k in ("cookie", "session", "unauthorized", "401", "403", "token")):
        return f"平台会话或 Cookie 已失效，请检查配置与设备环境 ({exc_str})"

    # 4. 网络连接 / 超时
    if any(k in exc_lower for k in ("timeout", "connection", "connect", "timed out", "unreachable")):
        return f"平台网络请求超时或网络连接失败 ({exc_str})"

    # 5. 已符合规范的前缀
    if any(exc_str.startswith(prefix) for prefix in ("签名节点", "平台", "红果", "番茄")):
        return exc_str

    # 6. 通用回退
    return f"平台 API 访问失败: {exc_str}"
