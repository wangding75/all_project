"""服务端配置（环境变量 / .env）。"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_repo_root() -> Path:
    """可写运行根：打包后为 exe 同级；开发时为仓库根。

    优先级:
      1. 环境变量 RESOURCE_DOWNLOAD_ROOT
      2. PyInstaller frozen → sys.executable 所在目录
      3. server/app/config.py → parents[2]（仓库根）
    """
    env = os.environ.get("RESOURCE_DOWNLOAD_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


REPO_ROOT = _resolve_repo_root()
DEFAULT_DATA_DIR = REPO_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


    api_key: str = "dev-key-change-me"
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1
    data_dir: Path = DEFAULT_DATA_DIR
    # 番茄章节间隔（秒）
    fanqie_delay: float = 1.0
    # 可选全局 Cookie（也可在创建 job 时 options.cookie 传入）
    fanqie_cookie: str = ""
    # Explicit CA bundle for Fanqie HTTPS; empty uses the system trust store.
    fanqie_ca_bundle: str = ""

    # 鉴权模式（阶段 D-0）：dev | dual | jwt_only
    # dev=仅 X-API-Key（默认，兼容 e2e）；dual=Key 或 JWT；jwt_only=仅 JWT
    auth_mode: Literal["dev", "dual", "jwt_only"] = "dev"
    # JWT（D-1 起生效；D-0 仅预留配置，Bearer 请求返回 501）
    jwt_secret: str = "change-me-jwt-secret"
    jwt_expire_minutes: int = 10080

    # 频率限制与每日配额（阶段 D-4）
    rate_limit_per_minute: int = 60
    rate_limit_auth_per_minute: int = 10
    free_jobs_per_day: int = 0
    vip_jobs_per_day: int = 50
    max_concurrent_jobs: int = 5
    max_queued_jobs: int = 100
    max_history_jobs: int = 200

    # Server-side launching is disabled by default; the desktop native bridge
    # opens downloaded files on the local machine.
    server_side_file_open: bool = False
    allow_server_file_open: bool = False

    # License Service（RD 独立 Service Credential；私钥只从 Secret 注入）
    license_service_base_url: str = ""
    license_service_key_id: str = ""
    license_service_private_key: str = ""
    license_service_audience: str = "rd"
    license_cache_ttl_seconds: int = 30
    license_service_timeout: float = 3.0
    license_service_verify: bool = True
    license_service_ca_bundle: str = ""
    license_service_client_cert: str = ""
    license_service_client_key: str = ""

    # Windows 客户端发布清单。未配置下载地址时更新检查保持关闭。
    client_latest_version: str = ""
    client_minimum_version: str = ""
    client_update_url: str = ""
    client_update_sha256: str = ""
    client_release_notes: str = ""
    client_update_mandatory: bool = False
    client_update_rollout_percentage: int = 100

    # ADB 与 Frida 配置（番茄 App 会话 / 书名搜索 / App 下载）
    adb_path: str = "adb"
    adb_device: str = "127.0.0.1:16384"  # 模拟器 adb 地址，务必与 adb devices 一致
    frida_host: str = "127.0.0.1:27042"
    fanqie_pkg: str = "com.dragon.read"
    hongguo_pkg: str = "com.phoenix.read"
    # 启动时探测设备运行时（agent + 各平台 App）
    fanqie_probe_on_startup: bool = True  # 兼容旧名：总开关，探测全部平台
    platform_probe_on_startup: bool = True
    fanqie_require_runtime: bool = False  # agent 缺失时拒绝启动
    require_platform_apps: bool = False  # 任一 App 未起时拒绝启动
    fanqie_try_start_agent: bool = True  # 尝试启动 sys_hlpd
    try_start_platform_apps: bool = True  # 尝试启动番茄/红果 App

    # 签名池配置（阶段 D-3）
    sign_pool_enabled: bool = False
    sign_pool_config: str = "data/sign_pool.json"
    sign_pool_urls: str = ""
    sign_pool_health_interval_sec: int = 30
    sign_pool_lease_sec: int = 120
    sign_pool_max_fails: int = 3

    @property
    def jobs_dir(self) -> Path:
        return self.data_dir / "jobs"

    @property
    def outputs_dir(self) -> Path:
        return self.data_dir / "outputs"

    @property
    def sign_pool_config_path(self) -> Path:
        p = Path(self.sign_pool_config)
        if p.is_absolute():
            return p
        return REPO_ROOT / p


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
