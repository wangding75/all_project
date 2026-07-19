"""HTTP 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app import __version__
from app.auth import require_api_key
from app.jobs import get_job_manager
from app.models import (
    DetailResponse,
    HealthResponse,
    JobCreateRequest,
    JobResponse,
    PlatformName,
    SearchItem,
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
    return await impl.search(q, page=page)


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
        return await impl.get_detail(id)
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


@api_router.get("/v1/files/{file_id:path}")
async def get_file(
    file_id: str,
    _: str = Depends(require_api_key),
) -> FileResponse:
    manager = get_job_manager()
    path = manager.resolve_file(file_id)
    if path is None:
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(path, filename=path.name)
