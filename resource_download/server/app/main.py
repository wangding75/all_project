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


from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 智能定位 UI 静态资源路径
if getattr(__import__("sys"), "frozen", False):
    UI_DIR = Path(__import__("sys")._MEIPASS) / "ui"
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
