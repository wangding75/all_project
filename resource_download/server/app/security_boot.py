"""E3 生产安全默认启动校验与脱敏工具。"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config import Settings

DEFAULT_API_KEY = "dev-key-change-me"
DEFAULT_JWT_SECRET = "change-me-jwt-secret"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def is_loopback_host(host: str) -> bool:
    """判断 Host 是否为本机 Loopback 地址。"""
    if not host:
        return False
    return host.strip().lower() in LOOPBACK_HOSTS


def mask_secret(val: str, keep_len: int = 4) -> str:
    """脱敏函数：禁止在日志中直接打印完整密码/密钥/Token/卡密。"""
    if not val:
        return ""
    if len(val) <= keep_len * 2:
        return "***"
    return f"{val[:keep_len]}***{val[-keep_len:]}"


def assert_production_secrets(settings: Settings) -> None:
    """校验生产安全配置 (E3 门闸)。

    规则：
    1. 当 AUTH_MODE 为 dual 或 jwt_only 时，若 JWT_SECRET 为默认值 ('change-me-jwt-secret') → 拒绝启动 (抛出 RuntimeError)。
    2. 当 API_KEY 为默认值 ('dev-key-change-me') 且 HOST 非 loopback (例如 0.0.0.0 或公网 IP) → 拒绝启动 (抛出 RuntimeError)。
    3. 仅当 AUTH_MODE=dev 且 HOST 为 loopback 本机网络时，允许使用默认 API Key 并在启动控制台输出 warning 警告。
    """
    mode = (settings.auth_mode or "dev").lower()
    host = settings.host or "127.0.0.1"

    if mode not in {"dev", "dual", "jwt_only"}:
        raise RuntimeError(
            f"AUTH_MODE must be one of dev, dual, jwt_only; got {settings.auth_mode!r}"
        )

    # 1. 检查 JWT 默认密钥 (dual / jwt_only 强制)
    if mode in ("dual", "jwt_only") and settings.jwt_secret == DEFAULT_JWT_SECRET:
        raise RuntimeError(
            f"🚫 [E3 生产安全阻断] 鉴权模式 AUTH_MODE={mode} 已启用，但 JWT_SECRET 仍为默认值 ('{DEFAULT_JWT_SECRET}')！"
            "\n【解决办法】请修改 .env 或环境变量中的 JWT_SECRET 为强随机密钥 (如 openssl rand -hex 32)。"
        )

    # 2. 检查默认 API Key 监听非本机
    if settings.api_key == DEFAULT_API_KEY and not is_loopback_host(host):
        raise RuntimeError(
            f"🚫 [E3 生产安全阻断] 服务正在监听非本机地址 HOST={host}，但 API_KEY 仍为默认开发 Key ('{DEFAULT_API_KEY}')！"
            "\n【解决办法】请修改 .env 或环境变量中的 API_KEY 为强随机密钥，或将 HOST 设为 127.0.0.1。"
        )

    # 3. 本机开发模式下的 warning 提示
    if settings.api_key == DEFAULT_API_KEY:
        logging.warning(
            "⚠️ [E3 开发警告] 当前使用的是默认开发 API Key ('dev-key-change-me')！在正式生产环境或对外提供服务时请通过 .env 覆盖。"
        )

    # License-Protected business must fail closed in production.  Local
    # loopback development may start without credentials, but its protected
    # routes still return a stable 503 rather than silently disabling the gate.
    license_production = not is_loopback_host(host)
    if license_production:
        missing = [
            name
            for name, value in (
                ("LICENSE_SERVICE_BASE_URL", settings.license_service_base_url),
                ("LICENSE_SERVICE_KEY_ID", settings.license_service_key_id),
                ("LICENSE_SERVICE_PRIVATE_KEY", settings.license_service_private_key),
            )
            if not str(value or "").strip()
        ]
        if missing:
            raise RuntimeError(
                "🚫 [T06 生产安全阻断] License Service 配置缺失："
                + ", ".join(missing)
                + "。受保护业务必须 fail-closed。"
            )
        if settings.license_service_audience != "rd":
            raise RuntimeError(
                "🚫 [T06 生产安全阻断] LICENSE_SERVICE_AUDIENCE 必须固定为 rd。"
            )
        if not settings.license_service_base_url.lower().startswith("https://"):
            raise RuntimeError(
                "🚫 [T06 生产安全阻断] 生产 License Service 必须使用 HTTPS。"
            )
        if not settings.license_service_verify:
            raise RuntimeError(
                "🚫 [T06 生产安全阻断] 生产 License Service 禁止关闭 TLS verify。"
            )

    if settings.jwt_secret == DEFAULT_JWT_SECRET and mode == "dev":
        logging.warning(
            "⚠️ [E3 开发警告] 当前使用的是默认 JWT 密钥 ('change-me-jwt-secret')！在启用 dual/jwt_only 商业模式前请通过 .env 覆盖。"
        )
