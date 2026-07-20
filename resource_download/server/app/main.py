"""FastAPI 入口。"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import api_router
from app.config import get_settings
from app.jobs import get_job_manager


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.jobs_dir.mkdir(parents=True, exist_ok=True)
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)

    # 初始化 SQLite 数据库
    from app.db import init_db
    init_db()

    if settings.api_key == "dev-key-change-me":
        logging.warning(
            "⚠️ 当前使用的是默认开发 API Key ('dev-key-change-me')！请在生产环境中通过 .env 或环境变量覆盖。"
        )

    if settings.jwt_secret == "change-me-jwt-secret" and settings.auth_mode in ("dual", "jwt_only"):
        logging.warning(
            "⚠️ 当前使用的是默认 JWT 密钥 ('change-me-jwt-secret') 且已启用用户鉴权！请在生产环境中通过 .env 或环境变量设置 JWT_SECRET。"
        )

    manager = get_job_manager()
    await manager.load_jobs()
    yield


app = FastAPI(
    title="Resource Download Relay",
    version=__version__,
    description="MVP-1 中转服务端：番茄/红果下载链路（脚本与 UI 验收）",
    lifespan=lifespan,
)
app.include_router(api_router)


# 智能定位 UI 静态资源路径
if getattr(sys, "frozen", False):
    UI_DIR = Path(sys._MEIPASS) / "ui"
else:
    UI_DIR = Path(__file__).resolve().parent.parent.parent / "ui"

if UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")


@app.get("/")
async def root():
    index_file = UI_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "service": "resource-download-relay",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
    }

