"""FastAPI 入口。"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import api_router
from app.config import get_settings
from app.jobs import get_job_manager
from app.sign_pool import SignPoolUnavailableError


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

    # E3 生产安全默认检查：若配置违规则直接抛错阻断进程启动
    from app.security_boot import assert_production_secrets
    assert_production_secrets(settings)

    manager = get_job_manager()
    await manager.load_jobs()

    if settings.sign_pool_enabled:
        from app.sign_pool import get_sign_pool

        get_sign_pool()
        logging.info("签名节点池已启用 (SIGN_POOL_ENABLED=True)")
    yield


app = FastAPI(
    title="Resource Download Relay",
    version=__version__,
    description="MVP-1 中转服务端：番茄/红果下载链路（脚本与 UI 验收）",
    lifespan=lifespan,
)


@app.exception_handler(SignPoolUnavailableError)
async def sign_pool_unavailable_exception_handler(_request: Request, exc: SignPoolUnavailableError):
    return JSONResponse(
        status_code=503,
        content={"detail": exc.message},
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

