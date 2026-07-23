"""服务端配置（环境变量 / .env）。"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

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

    # 鉴权模式（阶段 D-0）：dev | dual | jwt_only
    # dev=仅 X-API-Key（默认，兼容 e2e）；dual=Key 或 JWT；jwt_only=仅 JWT
    auth_mode: str = "dev"
    # JWT（D-1 起生效；D-0 仅预留配置，Bearer 请求返回 501）
    jwt_secret: str = "change-me-jwt-secret"
    jwt_expire_minutes: int = 10080

    # 频率限制与每日配额（阶段 D-4）
    rate_limit_per_minute: int = 60
    rate_limit_auth_per_minute: int = 10
    free_jobs_per_day: int = 0
    vip_jobs_per_day: int = 50

    # ADB 与 Frida 配置（番茄 App 会话）
    adb_path: str = "adb"
    adb_device: str = "127.0.0.1:16384"
    frida_host: str = "127.0.0.1:27042"
    fanqie_pkg: str = "com.dragon.read"

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
