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

    # 2. Vendor / 红果配置缺失
    if "hongguovendorerror" in exc_lower or "missing vendor" in exc_lower or "hongguo_config" in exc_lower:
        return f"红果 Vendor 组件未处于就绪状态: {exc_str}"
    if isinstance(exc, FileNotFoundError) and "hongguo_config" in exc_str.replace("\\", "/"):
        return (
            "缺少红果会话配置 data/config/hongguo_config.json。"
            "请运行: python tools/setup/grab_hongguo_config.py"
        )

    # 3. 会话 / 鉴权 / Cookie 失效
    if any(k in exc_lower for k in ("cookie", "session", "unauthorized", "401", "403", "token")):
        return f"平台会话或 Cookie 已失效，请检查配置与设备环境 ({exc_str})"

    # 4. 网络连接 / 超时
    if any(k in exc_lower for k in ("timeout", "connection", "connect", "timed out", "unreachable")):
        return f"平台网络请求超时或网络连接失败 ({exc_str})"

    # 5. 已符合规范的前缀
    if any(exc_str.startswith(prefix) for prefix in ("签名节点", "平台", "红果", "番茄")):
        return exc_str

    # 6. Frida 签名 RPC 失败（常为 agent/App 未就绪或会话僵死）
    if "rpcexception" in type(exc).__name__.lower() or exc_str in ("", "None", "none"):
        return (
            "平台签名失败（Frida RPC）。请确认：模拟器已连接、sys_hlpd 在跑、"
            "对应 App（番茄/红果）在前台；可重启 App 与 agent 后重试。"
            "红果还需 data/config/hongguo_config.json；番茄还需 fanqie_config.json。"
        )

    # 7. 通用回退
    return f"平台 API 访问失败: {exc_str}"
