"""FastAPI 入口。"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api import api_router
from app.config import get_settings
from app.jobs import get_job_manager


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.jobs_dir.mkdir(parents=True, exist_ok=True)
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    get_job_manager()
    yield


app = FastAPI(
    title="Resource Download Relay",
    version=__version__,
    description="MVP-1 中转服务端：番茄下载链路（脚本验收）",
    lifespan=lifespan,
)
app.include_router(api_router)


@app.get("/")
async def root() -> dict:
    return {
        "service": "resource-download-relay",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
    }
