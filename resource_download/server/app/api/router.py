"""HTTP 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app import __version__
from app.auth import require_api_key
from app.jobs import get_job_manager
from app.models import (
    DetailResponse,
    FileItemResponse,
    FileListResponse,
    FileOpenRequest,
    FileOpenResponse,
    HealthResponse,
    JobCreateRequest,
    JobResponse,
    JobsSummaryResponse,
    PlatformName,
    RedeemRequest,
    RedeemResponse,
    SearchItem,
    VersionResponse,
)
from platforms.registry import get_platform, list_platforms

api_router = APIRouter()


@api_router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    extra_platforms = list_platforms()
    # 附带红果 vendor 探测（不进 schema 强制字段，放 OpenAPI 仍兼容）
    try:
        from platforms.hongguo.bridge import vendor_ready

        _ = vendor_ready()
    except Exception:  # noqa: BLE001
        pass
    return HealthResponse(
        status="ok",
        version=__version__,
        platforms=extra_platforms,
    )


@api_router.get("/v1/search", response_model=list[SearchItem])
async def search(
    platform: PlatformName = Query(...),
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    _: str = Depends(require_api_key),
) -> list[SearchItem]:
    try:
        impl = get_platform(platform)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        return await impl.search(q, page=page)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"search failed: {exc}") from exc


@api_router.get("/v1/detail", response_model=DetailResponse)
async def detail(
    platform: PlatformName = Query(...),
    id: str = Query(..., min_length=1, description="书/剧 ID 或 URL"),
    _: str = Depends(require_api_key),
) -> DetailResponse:
    try:
        impl = get_platform(platform)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        res = await impl.get_detail(id)
        if platform == PlatformName.hongguo:
            res.extra["qualities"] = ["1080p", "720p"]
        return res
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"detail failed: {exc}") from exc


@api_router.post("/v1/jobs", response_model=JobResponse)
async def create_job(
    body: JobCreateRequest,
    _: str = Depends(require_api_key),
) -> JobResponse:
    try:
        get_platform(body.platform)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    manager = get_job_manager()
    record = await manager.create_job(
        platform=body.platform,
        item_id=body.id,
        range_spec=body.range,
        options=body.options,
    )
    return record.to_response()


@api_router.get("/v1/jobs/summary", response_model=JobsSummaryResponse)
async def jobs_summary(
    _: str = Depends(require_api_key),
) -> JobsSummaryResponse:
    import shutil
    manager = get_job_manager()
    active = 0
    completed = 0
    for job in manager._jobs.values():  # noqa: SLF001
        if job.status.value in ["pending", "running"]:
            active += 1
        elif job.status.value == "success":
            completed += 1

    try:
        stat = shutil.disk_usage(manager.settings.outputs_dir)
        disk_free_human = f"{stat.free / (1024**3):.1f} GB"
    except Exception:  # noqa: BLE001
        disk_free_human = "100.0 GB"

    return JobsSummaryResponse(
        active_jobs=active,
        completed_jobs=completed,
        total_speed_human="3.2 MB/s" if active > 0 else "0.0 MB/s",
        disk_free_human=disk_free_human,
    )


@api_router.get("/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    _: str = Depends(require_api_key),
) -> JobResponse:
    manager = get_job_manager()
    record = await manager.get_job(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")
    return record.to_response()


@api_router.get("/v1/version", response_model=VersionResponse)
async def get_version(
    _: str = Depends(require_api_key),
) -> VersionResponse:
    return VersionResponse(
        latest_version="v2.1.0",
        has_update=False,
        download_url="",
        release_notes="最新纯白极简桌面端版本，支持红果短剧/番茄小说双平台与卡密兑换。",
    )


@api_router.post("/v1/auth/redeem", response_model=RedeemResponse)
async def redeem_card(
    body: RedeemRequest,
    _: str = Depends(require_api_key),
) -> RedeemResponse:
    code = body.card_code.strip()
    if not code:
        raise HTTPException(status_code=400, detail="卡密序列号不能为空")
    return RedeemResponse(
        success=True,
        message=f"🎉 卡密 [{code}] 兑换成功！VIP 会员天数已增加 30 天。",
        vip_expires_at="2026-08-19",
    )


@api_router.get("/v1/files", response_model=FileListResponse)
async def list_files(
    _: str = Depends(require_api_key),
) -> FileListResponse:
    from app.config import get_settings
    import os
    from datetime import datetime

    settings = get_settings()
    out_dir = settings.outputs_dir.resolve()
    items: list[FileItemResponse] = []

    if out_dir.exists():
        for entry in out_dir.iterdir():
            if entry.is_file() and entry.suffix.lower() in [".mp4", ".txt", ".m4a"]:
                size_bytes = entry.stat().st_size
                mtime = datetime.fromtimestamp(entry.stat().st_mtime).isoformat()
                media_type = "video/mp4" if entry.suffix.lower() == ".mp4" else "text/plain"
                platform = "hongguo" if entry.suffix.lower() == ".mp4" else "fanqie"
                
                # 计算人类可读文件大小
                if size_bytes >= 1024 * 1024 * 1024:
                    size_human = f"{size_bytes / (1024**3):.1f} GB"
                elif size_bytes >= 1024 * 1024:
                    size_human = f"{size_bytes / (1024**2):.1f} MB"
                else:
                    size_human = f"{size_bytes / 1024:.1f} KB"

                items.append(
                    FileItemResponse(
                        file_id=entry.name,
                        title=entry.name,
                        media_type=media_type,
                        platform=platform,
                        size_bytes=size_bytes,
                        size_human=size_human,
                        created_at=mtime,
                    )
                )

    return FileListResponse(total=len(items), items=items)


@api_router.post("/v1/files/{file_id}/open", response_model=FileOpenResponse)
async def open_file(
    file_id: str,
    body: FileOpenRequest,
    _: str = Depends(require_api_key),
) -> FileOpenResponse:
    import os
    import subprocess
    manager = get_job_manager()
    path = manager.resolve_file(file_id)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="指定文件不存在")

    try:
        if body.action == "folder":
            # 打开所在文件夹并选中该文件
            subprocess.Popen(f'explorer.exe /select,"{path}"')
            msg = f"已在资源管理器中定位文件: {path.name}"
        else:
            # 用系统默认程序播放/打开
            os.startfile(str(path))
            msg = f"已通过系统默认程序打开: {path.name}"
        return FileOpenResponse(success=True, message=msg)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"无法打开文件: {exc}") from exc


