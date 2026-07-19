"""服务端配置（环境变量 / .env）。"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 仓库根目录: server/app/config.py -> parents[2]
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
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

    @property
    def jobs_dir(self) -> Path:
        return self.data_dir / "jobs"

    @property
    def outputs_dir(self) -> Path:
        return self.data_dir / "outputs"


def get_settings() -> Settings:
    return Settings()
