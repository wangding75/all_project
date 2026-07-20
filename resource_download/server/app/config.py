"""服务端配置（环境变量 / .env）。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 仓库根目录: server/app/config.py -> parents[2]
REPO_ROOT = Path(__file__).resolve().parents[2]
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
    data_dir: Path = DEFAULT_DATA_DIR
    # 番茄章节间隔（秒）
    fanqie_delay: float = 1.0
    # 可选全局 Cookie（也可在创建 job 时 options.cookie 传入）
    fanqie_cookie: str = ""

    # ADB 与 Frida 配置（番茄 App 会话）
    adb_path: str = r"D:\install\Netease\MuMu\nx_main\adb.exe"
    adb_device: str = "127.0.0.1:16384"
    frida_host: str = "127.0.0.1:27042"
    fanqie_pkg: str = "com.dragon.read"

    @property
    def jobs_dir(self) -> Path:
        return self.data_dir / "jobs"

    @property
    def outputs_dir(self) -> Path:
        return self.data_dir / "outputs"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
