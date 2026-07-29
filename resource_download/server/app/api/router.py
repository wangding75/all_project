"""HTTP 路由。"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app import __version__
from app.auth import Identity, require_identity, require_vip
from app.config import get_settings
from app.jobs import get_job_manager
from app.models import (
    BatchJobCreateRequest,
    BatchJobCreateResponse,
    BatchJobCreatedItem,
    BatchJobErrorItem,
    BatchJobSkippedItem,
    BatchResolveErrorItem,
    BatchResolveRequest,
    BatchResolveResponse,
    BatchResolvedItem,
    DetailResponse,
    FileItemResponse,
    FileListResponse,
    FileOpenRequest,
    FileOpenResponse,
    HealthDependencyItem,
    HealthResponse,
    JobCreateRequest,
    JobListResponse,
    JobResponse,
    JobsSummaryResponse,
    JobStatus,
    PlatformName,
    RedeemRequest,
    RedeemResponse,
    DiscoverResponse,
    DiscoverSection,
    SearchItem,
    SearchResponse,
    VersionResponse,
)
from platforms.registry import get_platform, list_platforms
from app.api.auth_router import auth_router
from app.api.admin import admin_router
from app.rate_limit import ip_rate_limiter
from app.db import get_db
from sqlalchemy.orm import Session

api_router = APIRouter(dependencies=[Depends(ip_rate_limiter("global"))])
api_router.include_router(auth_router)
api_router.include_router(admin_router)


@api_router.get("/v1/covers/{cover_id}.jpg", include_in_schema=False)
async def get_cached_cover(cover_id: str):
    """只允许读取发现接口预先登记的可信封面，不接受任意远程 URL。"""
    import asyncio

    from app.media_cache import materialize_cover

    try:
        path = await asyncio.to_thread(materialize_cover, cover_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"cover unavailable: {exc}") from exc
    if path is None or not path.is_file():
        raise HTTPException(status_code=404, detail="cover not found")
    return FileResponse(
        path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )




@api_router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """配置 + 设备运行时完整性检查（只探测不自启）。"""
    extra_platforms = list_platforms()
    runtime_report: dict | None = None
    settings = get_settings()
    include_runtime = settings.platform_probe_on_startup or settings.fanqie_probe_on_startup
    if include_runtime:
        try:
            from platforms.runtime import probe_all_runtimes

            runtime_report = probe_all_runtimes(try_start_agent=False, try_start_apps=False)
        except Exception as exc:  # noqa: BLE001
            runtime_report = {
                "ok": False,
                "degraded": True,
                "message": str(exc),
                "agent": {"ok": False, "adb_ok": False, "agent_running": False, "message": str(exc)},
                "fanqie_runtime": {},
                "hongguo_runtime": {},
            }

    from platforms.readiness import build_health_report

    report = build_health_report(include_runtime=include_runtime, runtime_report=runtime_report)
    checks = [
        HealthDependencyItem(
            key=str(c.get("key") or ""),
            label=str(c.get("label") or c.get("key") or ""),
            ok=bool(c.get("ok")),
            required=bool(c.get("required", True)),
            message=str(c.get("message") or ""),
            hints=list(c.get("hints") or []),
            detail=dict(c.get("detail") or {}),
        )
        for c in (report.get("checks") or [])
    ]

    return HealthResponse(
        status=str(report.get("status") or "ok"),
        version=__version__,
        platforms=extra_platforms,
        dependencies=report.get("dependencies") or {},
        checks=checks,
        summary=str(report.get("summary") or ""),
    )


def _version_tuple(value: str) -> tuple[int, ...]:
    import re

    parts = re.findall(r"\d+", str(value or ""))
    return tuple(int(part) for part in parts[:4]) or (0,)


@api_router.get("/v1/version", response_model=VersionResponse)
async def get_version(
    current_version: str = Query("", description="当前桌面客户端版本"),
    install_id: str = Query("", description="客户端安装实例 ID，用于稳定灰度"),
) -> VersionResponse:
    """返回可配置的 Windows 客户端发布清单。"""
    settings = get_settings()
    latest = settings.client_latest_version.strip() or __version__
    update_enabled = bool(settings.client_update_url.strip())
    has_update = bool(
        update_enabled
        and current_version.strip()
        and _version_tuple(latest) > _version_tuple(current_version)
    )
    rollout = max(0, min(100, settings.client_update_rollout_percentage))
    if has_update and rollout < 100 and install_id.strip():
        import hashlib

        bucket = int(hashlib.sha256(install_id.strip().encode("utf-8")).hexdigest()[:8], 16) % 100
        has_update = bucket < rollout
    minimum = settings.client_minimum_version.strip()
    mandatory = bool(settings.client_update_mandatory)
    if minimum and current_version.strip():
        mandatory = mandatory or _version_tuple(current_version) < _version_tuple(minimum)
    return VersionResponse(
        version=__version__,
        update_check_enabled=update_enabled,
        latest_version=latest,
        has_update=has_update,
        download_url=settings.client_update_url.strip() if has_update else "",
        sha256=settings.client_update_sha256.strip() if has_update else "",
        mandatory=mandatory if has_update else False,
        minimum_supported_version=minimum,
        rollout_percentage=rollout,
        release_notes=settings.client_release_notes.strip() or "当前已是最新版本。",
    )


_SOURCE_LABELS = {
    PlatformName.fanqie: "番茄小说",
    PlatformName.hongguo: "红果短剧",
}


def _tag_items(items: list[SearchItem], platform: PlatformName) -> list[SearchItem]:
    """确保每条结果带有 platform / source_label。"""
    label = _SOURCE_LABELS.get(platform, platform.value)
    out: list[SearchItem] = []
    for it in items:
        data = it.model_dump() if hasattr(it, "model_dump") else dict(it)
        if not data.get("platform"):
            data["platform"] = platform
        if not data.get("source_label"):
            data["source_label"] = label
        out.append(SearchItem(**data))
    return out


async def _search_one(platform: PlatformName, q: str, page: int) -> tuple[list[SearchItem], str | None]:
    """单平台搜索；失败返回 ([], error_message) 不抛。"""
    try:
        impl = get_platform(platform)
    except (NotImplementedError, KeyError) as exc:
        return [], str(exc)
    try:
        items = await impl.search(q, page=page)
        return _tag_items(list(items or []), platform), None
    except Exception as exc:  # noqa: BLE001
        return [], f"{platform.value}: {exc}"


@api_router.get("/v1/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1),
    platform: str | None = Query(
        None,
        description="fanqie | hongguo | all；省略或 all 时聚合双平台搜索",
    ),
    page: int = Query(1, ge=1),
    _: Identity = Depends(require_identity),
) -> SearchResponse:
    """单平台或聚合搜索。聚合时某平台失败仍返回另一平台结果，错误写在 platform_errors。"""
    import asyncio

    raw = (platform or "all").strip().lower()
    if raw in {"", "all", "*"}:
        targets = [PlatformName.fanqie, PlatformName.hongguo]
    elif raw in {PlatformName.fanqie.value, PlatformName.hongguo.value}:
        targets = [PlatformName(raw)]
    else:
        raise HTTPException(
            status_code=400,
            detail=f"unknown platform: {platform!r}，可选 fanqie / hongguo / all",
        )

    results = await asyncio.gather(*[_search_one(p, q, page) for p in targets])
    items: list[SearchItem] = []
    errors: dict[str, str] = {}
    for p, (plist, err) in zip(targets, results):
        if err:
            errors[p.value] = err
        items.extend(plist)

    # 单平台且完全失败 → 502，与旧行为一致
    if len(targets) == 1 and not items and errors:
        raise HTTPException(status_code=502, detail=f"search failed: {next(iter(errors.values()))}")

    return SearchResponse(
        items=items,
        platforms_queried=[p.value for p in targets],
        platform_errors=errors,
        total=len(items),
        page=page,
        page_size=20,
        has_more=any(len(platform_items) >= 20 for platform_items, _error in results),
    )


@api_router.post("/v1/batch/resolve", response_model=BatchResolveResponse)
async def resolve_batch(
    body: BatchResolveRequest,
    _: Identity = Depends(require_identity),
) -> BatchResolveResponse:
    """批量识别链接或资源 ID；单条失败不会中断整批。"""
    import asyncio

    semaphore = asyncio.Semaphore(5)

    def _targets(raw_input: str) -> list[PlatformName]:
        if body.platform_hint != "all":
            return [PlatformName(body.platform_hint)]
        lowered = raw_input.lower()
        if "fanqienovel.com" in lowered or "com.dragon.read" in lowered:
            return [PlatformName.fanqie]
        if "hongguo" in lowered or "com.phoenix.read" in lowered:
            return [PlatformName.hongguo]
        return [PlatformName.hongguo, PlatformName.fanqie]

    async def _resolve(raw_input: str):
        value = raw_input.strip()
        if not value:
            return None, BatchResolveErrorItem(
                input=raw_input,
                code="INVALID_INPUT",
                message="输入不能为空",
            )
        async with semaphore:
            candidates = _targets(value)
            results = await asyncio.gather(
                *[_search_one(platform_name, value, 1) for platform_name in candidates]
            )
        errors = []
        for platform_name, (items, error) in zip(candidates, results):
            if items:
                return BatchResolvedItem(input=raw_input, content=items[0]), None
            if error:
                errors.append(f"{platform_name.value}: {error}")
        return None, BatchResolveErrorItem(
            input=raw_input,
            code="NOT_FOUND",
            message="；".join(errors) or "未找到对应资源",
        )

    results = await asyncio.gather(*[_resolve(value) for value in body.inputs])
    items = [item for item, _error in results if item is not None]
    errors = [error for _item, error in results if error is not None]
    return BatchResolveResponse(items=items, errors=errors)


@api_router.get("/v1/discover", response_model=DiscoverResponse)
async def discover(
    platform: str | None = Query(
        None,
        description="fanqie | hongguo | all；默认 all",
    ),
    kinds: str = Query(
        "hot,new",
        description="逗号分隔：hot=热榜, new=今日/近期上新",
    ),
    limit: int = Query(24, ge=1, le=50),
    _: Identity = Depends(require_identity),
) -> DiscoverResponse:
    """首页发现页：聚合平台真实热榜 / 今日上新，单平台失败时降级返回。"""
    raw = (platform or "all").strip().lower()
    if raw in {"", "all", "*"}:
        targets = [PlatformName.fanqie, PlatformName.hongguo]
    elif raw in {PlatformName.fanqie.value, PlatformName.hongguo.value}:
        targets = [PlatformName(raw)]
    else:
        raise HTTPException(
            status_code=400,
            detail=f"unknown platform: {platform!r}，可选 fanqie / hongguo / all",
        )

    kind_list = [k.strip().lower() for k in (kinds or "hot,new").split(",") if k.strip()]
    if not kind_list:
        kind_list = ["hot", "new"]
    invalid_kinds = [kind for kind in kind_list if kind not in {"hot", "new"}]
    if invalid_kinds:
        raise HTTPException(status_code=400, detail=f"unsupported discover kinds: {invalid_kinds}")

    title_map = {
        "hot": "🔥 热榜",
        "new": "✨ 今日上新",
    }
    plat_labels = {
        PlatformName.fanqie: "番茄小说",
        PlatformName.hongguo: "红果短剧",
    }
    plat_hint = (
        "、".join(plat_labels.get(p, p.value) for p in targets)
        if len(targets) > 1
        else plat_labels.get(targets[0], targets[0].value)
    )

    import asyncio

    async def _load(platform_name: PlatformName, kind: str):
        try:
            impl = get_platform(platform_name)
            items = await impl.discover(kind, limit=limit)
            from app.media_cache import register_cover_url

            for item in items or []:
                proxied = register_cover_url(item.cover)
                if proxied:
                    item.cover = proxied
            return platform_name, list(items or []), None
        except Exception as exc:  # noqa: BLE001
            return platform_name, [], str(exc)

    sections: list[DiscoverSection] = []
    any_live = False
    for kind in kind_list:
        results = await asyncio.gather(*[_load(target, kind) for target in targets])
        items = []
        errors: dict[str, str] = {}
        successful_platforms = 0
        for platform_name, platform_items, error in results:
            if error:
                errors[platform_name.value] = error
            else:
                successful_platforms += 1
                items.extend(platform_items)
        available = successful_platforms > 0
        any_live = any_live or available
        sections.append(
            DiscoverSection(
                kind=kind,
                title=title_map[kind],
                items=items,
                available=available,
                message=(
                    f"{plat_hint}暂未返回{title_map[kind]}内容"
                    if available
                    else f"{plat_hint}{title_map[kind]}暂不可用"
                ),
                platform_errors=errors,
            )
        )

    return DiscoverResponse(
        sections=sections,
        platforms_queried=[p.value for p in targets],
        data_mode="live" if any_live else "unavailable",
        note=(
            f"{plat_hint}发现内容已更新"
            if any_live
            else f"{plat_hint}发现内容当前不可用，可继续使用资源搜索"
        ),
    )


@api_router.get("/v1/detail", response_model=DetailResponse)
async def detail(
    platform: PlatformName = Query(...),
    id: str = Query(..., min_length=1, description="书/剧 ID 或 URL"),
    page: int | None = Query(None, ge=1, description="可选选集页码"),
    page_size: int | None = Query(None, ge=1, le=500, description="可选每页选集数量"),
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
            res.extra["qualities"] = ["1080p"]
            res.extra["quality_note"] = (
                "360p/480p/540p/720p use proprietary ByteVC2 and are not exposed "
                "as playable downloads"
            )

        if page is not None and page_size is not None:
            total_segments = len(res.segments)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            res.extra["total_segments"] = total_segments
            res.extra["page"] = page
            res.extra["page_size"] = page_size
            res.segments = res.segments[start_idx:end_idx]

        return res
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"detail failed: {exc}") from exc


@api_router.post("/v1/jobs", response_model=JobResponse)
async def create_job(
    body: JobCreateRequest,
    identity: Identity = Depends(require_vip),
    db: Session = Depends(get_db),
) -> JobResponse:
    try:
        get_platform(body.platform)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # 每日配额校验
    from app.quota import check_job_quota, increment_job_quota
    check_job_quota(identity, db)

    owner_user_id = identity.user_id if identity.kind == "user" else None
    owner_kind = identity.kind if identity.kind == "user" else "ops"

    manager = get_job_manager()
    try:
        record = await manager.create_job(
            platform=body.platform,
            item_id=body.id,
            range_spec=body.range,
            options=body.options,
            owner_user_id=owner_user_id,
            owner_kind=owner_kind,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    # 创建成功后累加配额计数
    increment_job_quota(identity, db)
    return record.to_response()


@api_router.post("/v1/jobs/batch", response_model=BatchJobCreateResponse)
async def create_jobs_batch(
    body: BatchJobCreateRequest,
    identity: Identity = Depends(require_vip),
    db: Session = Depends(get_db),
) -> BatchJobCreateResponse:
    """批量创建任务；逐项返回 created/skipped/errors，不因单项失败回滚整批。"""
    import uuid

    from app.quota import check_job_quota, increment_job_quota

    manager = get_job_manager()
    owner_user_id = identity.user_id if identity.kind == "user" else None
    owner_kind = identity.kind if identity.kind == "user" else "ops"
    existing, _ = await manager.list_jobs_for(identity, page=1, page_size=1000)
    existing_by_key: dict[tuple[PlatformName, str], list] = {}
    for record in existing:
        existing_by_key.setdefault((record.platform, record.item_id), []).append(record)

    created: list[BatchJobCreatedItem] = []
    skipped: list[BatchJobSkippedItem] = []
    errors: list[BatchJobErrorItem] = []

    for item in body.items:
        key = (item.platform, item.id)
        prior = existing_by_key.get(key, [])
        completed = next((job for job in prior if job.status == JobStatus.success), None)
        if body.duplicate_policy == "skip_completed" and completed is not None:
            skipped.append(
                BatchJobSkippedItem(
                    item_id=item.id,
                    platform=item.platform,
                    reason="already_completed",
                    existing_job_id=completed.job_id,
                )
            )
            continue

        try:
            get_platform(item.platform)
            check_job_quota(identity, db)
            record = await manager.create_job(
                platform=item.platform,
                item_id=item.id,
                range_spec=item.range,
                options=item.options,
                max_active=get_settings().max_queued_jobs,
                owner_user_id=owner_user_id,
                owner_kind=owner_kind,
            )
            increment_job_quota(identity, db)
            existing_by_key.setdefault(key, []).append(record)
            created.append(
                BatchJobCreatedItem(
                    item_id=item.id,
                    platform=item.platform,
                    job_id=record.job_id,
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(
                BatchJobErrorItem(
                    item_id=item.id,
                    platform=item.platform,
                    message=str(getattr(exc, "detail", exc)),
                )
            )

    return BatchJobCreateResponse(
        batch_id=f"batch-{uuid.uuid4().hex[:12]}",
        created=created,
        skipped=skipped,
        errors=errors,
    )


@api_router.get("/v1/jobs", response_model=JobListResponse)
async def list_jobs(
    status: JobStatus | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    identity: Identity = Depends(require_identity),
) -> JobListResponse:
    manager = get_job_manager()
    records, total = await manager.list_jobs_for(identity, status=status, page=page, page_size=page_size)
    return JobListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[r.to_response() for r in records],
    )


@api_router.get("/v1/jobs/summary", response_model=JobsSummaryResponse)
async def jobs_summary(
    identity: Identity = Depends(require_identity),
) -> JobsSummaryResponse:
    manager = get_job_manager()
    data = await manager.summary_for(identity)
    return JobsSummaryResponse(**data)


@api_router.get("/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    identity: Identity = Depends(require_identity),
) -> JobResponse:
    manager = get_job_manager()
    record = await manager.get_job_for(job_id, identity)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")
    return record.to_response()


@api_router.delete("/v1/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    identity: Identity = Depends(require_identity),
) -> dict[str, str]:
    manager = get_job_manager()
    record = await manager.get_job_for(job_id, identity)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")

    cancelled = await manager.cancel_job_for(job_id, identity)
    if not cancelled:
        raise HTTPException(status_code=400, detail="Job 无法取消（可能已完成、已失败或不存在）")
    return {"message": "Job successfully cancelled", "job_id": job_id}


@api_router.get("/v1/files", response_model=FileListResponse)
async def list_files(
    identity: Identity = Depends(require_identity),
) -> FileListResponse:
    manager = get_job_manager()
    settings = get_settings()
    out_dir = settings.outputs_dir.resolve()
    items: list[FileItemResponse] = []

    if out_dir.exists():
        for entry in out_dir.rglob("*"):
            ext = entry.suffix.lower()
            if entry.is_file() and ext in [".mp4", ".txt", ".m4a"]:
                rel_id = str(entry.relative_to(out_dir)).replace("\\", "/")
                if not manager.can_access_file(rel_id, identity):
                    continue

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


@api_router.get("/v1/files/thumbnail")
async def get_file_thumbnail(
    file_id: str = Query(..., min_length=1),
    identity: Identity = Depends(require_identity),
) -> FileResponse:
    """生成或读取媒体缩略图；视频抽帧，小说优先使用同目录真实封面。"""
    import asyncio
    import hashlib
    import shutil

    manager = get_job_manager()
    if not manager.can_access_file(file_id, identity):
        raise HTTPException(status_code=404, detail="指定文件不存在")
    source = manager.resolve_file(file_id)
    if source is None or not source.is_file():
        raise HTTPException(status_code=404, detail="指定文件不存在")

    cache_dir = get_settings().data_dir / "cache" / "thumbnails"
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f"{source.resolve()}:{source.stat().st_mtime_ns}".encode()).hexdigest()
    target = cache_dir / f"{key}.jpg"

    def _materialize() -> None:
        if target.is_file() and target.stat().st_size > 0:
            return
        cover = next(
            (
                path
                for path in (source.parent / "封面.jpg", source.parent.parent / "封面.jpg")
                if path.is_file()
            ),
            None,
        )
        if cover is not None:
            shutil.copyfile(cover, target)
            return
        if source.suffix.lower() != ".mp4":
            return
        ffmpeg = os.environ.get("FFMPEG_BINARY") or shutil.which("ffmpeg")
        if not ffmpeg:
            try:
                import imageio_ffmpeg

                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                ffmpeg = None
        if not ffmpeg:
            return
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-ss",
                "00:00:01",
                "-i",
                str(source),
                "-frames:v",
                "1",
                "-vf",
                "scale=360:-2",
                str(target),
            ],
            capture_output=True,
            timeout=30,
        )

    await asyncio.to_thread(_materialize)
    if not target.is_file() or target.stat().st_size == 0:
        raise HTTPException(status_code=404, detail="该资源暂无可用缩略图")
    return FileResponse(target, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=86400"})


@api_router.get("/v1/files/{file_id:path}")
async def get_file(
    file_id: str,
    identity: Identity = Depends(require_identity),
) -> FileResponse:
    manager = get_job_manager()
    if not manager.can_access_file(file_id, identity):
        raise HTTPException(status_code=404, detail="指定文件不存在")
    path = manager.resolve_file(file_id)
    if path is None or not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="指定文件不存在")
    return FileResponse(path=path, filename=path.name)


@api_router.post("/v1/files/{file_id:path}/open", response_model=FileOpenResponse)
async def open_file(
    file_id: str,
    body: FileOpenRequest,
    identity: Identity = Depends(require_identity),
) -> FileOpenResponse:
    manager = get_job_manager()
    if not manager.can_access_file(file_id, identity):
        raise HTTPException(status_code=404, detail="指定文件或目录不存在")
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


@api_router.get("/v1/admin/sign-pool")
async def admin_sign_pool(
    identity: Identity = Depends(require_identity),
) -> dict[str, Any]:
    if not identity.is_ops:
        raise HTTPException(status_code=403, detail="仅 API Key 运维权限可访问此接口")
    from app.sign_pool import get_sign_pool

    return get_sign_pool().get_summary()





