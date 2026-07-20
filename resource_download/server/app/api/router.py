"""HTTP 路由。"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app import __version__
from app.auth import Identity, require_identity
from app.config import get_settings
from app.jobs import get_job_manager
from app.models import (
    DetailResponse,
    FileItemResponse,
    FileListResponse,
    FileOpenRequest,
    FileOpenResponse,
    HealthResponse,
    JobCreateRequest,
    JobListResponse,
    JobResponse,
    JobsSummaryResponse,
    JobStatus,
    PlatformName,
    RedeemRequest,
    RedeemResponse,
    SearchItem,
    VersionResponse,
)
from platforms.registry import get_platform, list_platforms
from app.api.auth_router import auth_router

api_router = APIRouter()
api_router.include_router(auth_router)



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
    _: Identity = Depends(require_identity),
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
    _: Identity = Depends(require_identity),
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
    _: Identity = Depends(require_identity),
) -> JobResponse:
    try:
        get_platform(body.platform)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    manager = get_job_manager()
    try:
        record = await manager.create_job(
            platform=body.platform,
            item_id=body.id,
            range_spec=body.range,
            options=body.options,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    return record.to_response()


@api_router.get("/v1/jobs", response_model=JobListResponse)
async def list_jobs(
    status: JobStatus | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: Identity = Depends(require_identity),
) -> JobListResponse:
    manager = get_job_manager()
    records, total = await manager.list_jobs(status=status, page=page, page_size=page_size)
    return JobListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[r.to_response() for r in records],
    )


@api_router.get("/v1/jobs/summary", response_model=JobsSummaryResponse)
async def jobs_summary(
    _: Identity = Depends(require_identity),
) -> JobsSummaryResponse:
    manager = get_job_manager()
    data = await manager.summary()
    return JobsSummaryResponse(**data)


@api_router.get("/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    _: Identity = Depends(require_identity),
) -> JobResponse:
    manager = get_job_manager()
    record = await manager.get_job(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")
    return record.to_response()


@api_router.delete("/v1/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    _: Identity = Depends(require_identity),
) -> dict[str, str]:
    manager = get_job_manager()
    cancelled = await manager.cancel_job(job_id)
    if not cancelled:
        raise HTTPException(status_code=400, detail="Job 无法取消（可能已完成、已失败或不存在）")
    return {"message": "Job successfully cancelled", "job_id": job_id}


@api_router.get("/v1/version", response_model=VersionResponse)
async def get_version(
    _: Identity = Depends(require_identity),
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
    _: Identity = Depends(require_identity),
) -> RedeemResponse:
    code = body.card_code.strip()
    if not code:
        raise HTTPException(status_code=400, detail="卡密序列号不能为空")
    return RedeemResponse(
        success=False,
        message=f"卡密兑换功能暂未开启（商业化 Stub）。序列号 [{code}] 暂无法兑换。",
        vip_expires_at="",
    )


@api_router.get("/v1/files", response_model=FileListResponse)
async def list_files(
    _: Identity = Depends(require_identity),
) -> FileListResponse:
    settings = get_settings()
    out_dir = settings.outputs_dir.resolve()
    items: list[FileItemResponse] = []

    if out_dir.exists():
        for entry in out_dir.rglob("*"):
            ext = entry.suffix.lower()
            if entry.is_file() and ext in [".mp4", ".txt", ".m4a"]:
                size_bytes = entry.stat().st_size
                mtime = datetime.fromtimestamp(entry.stat().st_mtime).isoformat()
                if ext == ".mp4":
                    media_type = "video/mp4"
                    platform = "hongguo"
                elif ext == ".m4a":
                    media_type = "audio/mp4"
                    platform = "hongguo"
                else:
                    media_type = "text/plain"
                    platform = "fanqie"

                rel_id = str(entry.relative_to(out_dir)).replace("\\", "/")

                # 计算人类可读文件大小
                if size_bytes >= 1024 * 1024 * 1024:
                    size_human = f"{size_bytes / (1024**3):.1f} GB"
                elif size_bytes >= 1024 * 1024:
                    size_human = f"{size_bytes / (1024**2):.1f} MB"
                else:
                    size_human = f"{size_bytes / 1024:.1f} KB"

                items.append(
                    FileItemResponse(
                        file_id=rel_id,
                        title=entry.name,
                        media_type=media_type,
                        platform=platform,
                        size_bytes=size_bytes,
                        size_human=size_human,
                        created_at=mtime,
                    )
                )

    return FileListResponse(total=len(items), items=items)


@api_router.get("/v1/files/{file_id:path}")
async def get_file(
    file_id: str,
    _: Identity = Depends(require_identity),
) -> FileResponse:
    manager = get_job_manager()
    path = manager.resolve_file(file_id)
    if path is None or not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="指定文件不存在")
    return FileResponse(path=path, filename=path.name)


@api_router.post("/v1/files/{file_id:path}/open", response_model=FileOpenResponse)
async def open_file(
    file_id: str,
    body: FileOpenRequest,
    _: Identity = Depends(require_identity),
) -> FileOpenResponse:
    manager = get_job_manager()
    path = manager.resolve_file(file_id)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="指定文件或目录不存在")

    try:
        if body.action == "folder":
            if path.is_file():
                # 打开所在文件夹并选中该文件 (含空格路径用引号包裹)
                subprocess.Popen(["explorer.exe", f'/select,"{path}"'])
                msg = f"已在资源管理器中定位文件: {path.name}"
            else:
                # 路径本身为目录，直接在资源管理器中打开
                subprocess.Popen(["explorer.exe", str(path)])
                msg = f"已在资源管理器中打开目录: {path.name or 'outputs'}"
        else:
            os.startfile(str(path))
            msg = f"已成功通过系统程序打开: {path.name or 'outputs'}"
        return FileOpenResponse(success=True, message=msg)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"无法打开文件或目录: {exc}") from exc




