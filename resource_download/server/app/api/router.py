"""HTTP 路由。"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse

from app import __version__
from app.auth import Identity, require_identity
from app.errors import format_platform_error, sanitize_error_text
from app.config import get_settings
from app.jobs import get_job_manager
from app.license_guard import require_active_device_license
from app.license_gateway import LicenseGateway, get_license_gateway
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
    HongguoMonitorConfig,
    HongguoMonitorStatus,
    ImageRecognizeRequest,
    ImageRecognizeResponse,
    PeopleResponse,
    PlatformName,
    QueueBulkActionRequest,
    QueueBulkRequest,
    QueueBulkResponse,
    QueueReorderRequest,
    QueueStateResponse,
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


def _public_health_value(value: Any) -> Any:
    """Strip local filesystem topology from the public health document."""
    hidden_keys = {"path", "vendor_path", "config_path", "agent_bin"}
    if isinstance(value, dict):
        return {
            str(key): _public_health_value(item)
            for key, item in value.items()
            if str(key).lower() not in hidden_keys
        }
    if isinstance(value, list):
        return [_public_health_value(item) for item in value]
    if isinstance(value, str) and (":\\" in value or value.startswith("/")):
        return "<redacted>"
    return value


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
                "message": sanitize_error_text(exc),
                "agent": {"ok": False, "adb_ok": False, "agent_running": False, "message": sanitize_error_text(exc)},
                "fanqie_runtime": {},
                "hongguo_runtime": {},
            }

    from platforms.readiness import build_health_report

    report = _public_health_value(
        build_health_report(include_runtime=include_runtime, runtime_report=runtime_report)
    )
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
        return [], sanitize_error_text(exc)
    try:
        items = await impl.search(q, page=page)
        return _tag_items(list(items or []), platform), None
    except Exception as exc:  # noqa: BLE001
        return [], f"{platform.value}: {format_platform_error(exc)}"


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


@api_router.post("/v1/image/recognize", response_model=ImageRecognizeResponse)
async def recognize_image(
    body: ImageRecognizeRequest,
    _: Identity = Depends(require_identity),
) -> ImageRecognizeResponse:
    from app.image_recognition import decode_image_base64, recognize_cover

    try:
        image_data = decode_image_base64(body.image_base64)
        return await recognize_cover(
            image_data,
            platform_hint=body.platform_hint,
            max_candidates=body.max_candidates,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=sanitize_error_text(exc)) from exc


@api_router.get("/v1/hongguo/people", response_model=PeopleResponse)
async def hongguo_people(
    genre: str = Query("short_play"),
    work_limit: int = Query(20, ge=1, le=30),
    _: Identity = Depends(require_identity),
) -> PeopleResponse:
    if genre not in {"short_play", "comic_series", "ai_series"}:
        raise HTTPException(status_code=400, detail=f"unsupported hongguo genre: {genre}")
    platform = get_platform(PlatformName.hongguo)
    if not hasattr(platform, "get_people_index"):
        raise HTTPException(status_code=501, detail="当前红果适配器不支持演职员索引")
    try:
        result = await platform.get_people_index(genre=genre, work_limit=work_limit)
        from app.media_cache import register_cover_url

        for person in result.people:
            person.avatar = register_cover_url(person.avatar)
            for work in person.works:
                work.cover = register_cover_url(work.cover)
        return result
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"people index failed: {exc}") from exc


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
    genre: str = Query(
        "short_play",
        description="红果体裁：short_play | comic_series | ai_series",
    ),
    sort: str = Query(
        "hot_score",
        description="红果排序：hot_score | online_time | hot_collect",
    ),
    theme: str | None = Query(None, max_length=30),
    setting: str | None = Query(None, max_length=30),
    background: str | None = Query(None, max_length=30),
    gender: str | None = Query(None, max_length=10),
    days: int | None = Query(None, ge=1, le=90),
    creation_status: str | None = Query(None, max_length=20),
    min_episode_count: int = Query(0, ge=0, le=10000),
    keyword: str | None = Query(None, max_length=50),
    only_today: bool = Query(True),
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
    allowed_genres = {"short_play", "comic_series", "ai_series"}
    if genre not in allowed_genres:
        raise HTTPException(status_code=400, detail=f"unsupported hongguo genre: {genre}")
    allowed_sorts = {"hot_score", "online_time", "hot_collect"}
    if sort not in allowed_sorts:
        raise HTTPException(status_code=400, detail=f"unsupported hongguo sort: {sort}")
    if days is not None and days not in {7, 14, 30, 90}:
        raise HTTPException(status_code=400, detail="days must be one of 7, 14, 30, 90")
    if gender not in {None, "", "男频", "女频", "1", "0"}:
        raise HTTPException(status_code=400, detail="unsupported gender")
    if creation_status not in {None, "", "已完结", "连载中", "完结", "连载"}:
        raise HTTPException(status_code=400, detail="unsupported creation_status")

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
            items = await impl.discover(
                kind,
                limit=limit,
                genre=genre,
                sort=sort,
                theme=theme,
                setting=setting,
                background=background,
                gender=gender,
                days=days,
                status=creation_status,
                only_today=only_today,
            )
            from app.media_cache import register_cover_url

            filtered_items = []
            normalized_keyword = (keyword or "").strip().lower()
            for item in items or []:
                try:
                    episode_count = int(item.extra.get("episode_count") or 0)
                except (TypeError, ValueError):
                    episode_count = 0
                if min_episode_count and episode_count < min_episode_count:
                    continue
                if normalized_keyword:
                    haystack = " ".join(
                        [
                            str(item.title or ""),
                            str(item.author or ""),
                            str(item.desc or ""),
                            str(item.extra.get("category") or ""),
                        ]
                    ).lower()
                    if normalized_keyword not in haystack:
                        continue
                proxied = register_cover_url(item.cover)
                if proxied:
                    item.cover = proxied
                filtered_items.append(item)
            return platform_name, filtered_items, None
        except Exception as exc:  # noqa: BLE001
            return platform_name, [], sanitize_error_text(exc)

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
        raise HTTPException(status_code=501, detail=sanitize_error_text(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=sanitize_error_text(exc)) from exc
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
        raise HTTPException(
            status_code=502,
            detail=f"detail failed: {format_platform_error(exc)}",
        ) from exc


@api_router.post("/v1/jobs", response_model=JobResponse)
async def create_job(
    body: JobCreateRequest,
    identity: Identity = Depends(require_active_device_license),
    db: Session = Depends(get_db),
) -> JobResponse:
    try:
        get_platform(body.platform)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=sanitize_error_text(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=sanitize_error_text(exc)) from exc

    # 每日配额校验
    from app.quota import check_job_quota, increment_job_quota, release_job_quota
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
        release_job_quota(identity)
        raise HTTPException(status_code=429, detail=sanitize_error_text(exc)) from exc
    except ValueError as exc:
        release_job_quota(identity)
        raise HTTPException(status_code=422, detail=sanitize_error_text(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        release_job_quota(identity)
        raise HTTPException(status_code=500, detail="job creation failed") from exc

    # 创建成功后累加配额计数
    increment_job_quota(identity, db)
    return record.to_response()


@api_router.post("/v1/jobs/batch", response_model=BatchJobCreateResponse)
async def create_jobs_batch(
    body: BatchJobCreateRequest,
    identity: Identity = Depends(require_active_device_license),
    db: Session = Depends(get_db),
) -> BatchJobCreateResponse:
    """批量创建任务；逐项返回 created/skipped/errors，不因单项失败回滚整批。"""
    import uuid

    from app.quota import check_job_quota, increment_job_quota, release_job_quota

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
            reserved = True
            record = await manager.create_job(
                platform=item.platform,
                item_id=item.id,
                range_spec=item.range,
                options=item.options,
                max_active=get_settings().max_queued_jobs,
                owner_user_id=owner_user_id,
                owner_kind=owner_kind,
                priority=body.queue_mode == "start_immediately",
            )
            increment_job_quota(identity, db)
            reserved = False
            existing_by_key.setdefault(key, []).append(record)
            created.append(
                BatchJobCreatedItem(
                    item_id=item.id,
                    platform=item.platform,
                    job_id=record.job_id,
                )
            )
        except Exception as exc:  # noqa: BLE001
            if "reserved" in locals() and reserved:
                release_job_quota(identity)
            errors.append(
                BatchJobErrorItem(
                    item_id=item.id,
                    platform=item.platform,
                    message=sanitize_error_text(getattr(exc, "detail", exc)),
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


@api_router.get("/v1/jobs/queue", response_model=QueueStateResponse)
async def get_queue(
    identity: Identity = Depends(require_identity),
) -> QueueStateResponse:
    return QueueStateResponse(**await get_job_manager().queue_state_for(identity))


@api_router.post("/v1/jobs/queue/pause")
async def pause_queue(
    identity: Identity = Depends(require_identity),
) -> dict[str, Any]:
    count = await get_job_manager().pause_queue_for(identity)
    return {"paused": True, "affected": count}


@api_router.post("/v1/jobs/queue/resume")
async def resume_queue(
    identity: Identity = Depends(require_identity),
) -> dict[str, Any]:
    count = await get_job_manager().resume_queue_for(identity)
    return {"paused": False, "affected": count}


@api_router.post("/v1/jobs/queue/reorder")
async def reorder_queue(
    body: QueueReorderRequest,
    identity: Identity = Depends(require_identity),
) -> dict[str, Any]:
    ok = await get_job_manager().reorder_queue_for(identity, body.job_ids)
    if not ok:
        raise HTTPException(status_code=400, detail="队列包含不存在、运行中或无权操作的任务")
    return {"success": True, "job_ids": body.job_ids}


@api_router.post("/v1/jobs/queue/bulk", response_model=QueueBulkResponse)
async def bulk_queue_action(
    body: QueueBulkActionRequest,
    identity: Identity = Depends(require_identity),
) -> QueueBulkResponse:
    manager = get_job_manager()
    requested = list(dict.fromkeys(body.job_ids))
    if body.action == "pause":
        changed, skipped = await manager.set_jobs_paused_for(
            identity,
            requested,
            paused=True,
        )
    elif body.action == "resume":
        changed, skipped = await manager.set_jobs_paused_for(
            identity,
            requested,
            paused=False,
        )
    elif body.action == "archive":
        changed, skipped = await manager.archive_jobs_for(identity, requested)
    else:
        changed = []
        skipped = []
        for job_id in requested:
            if await manager.cancel_job_for(job_id, identity):
                changed.append(job_id)
            else:
                skipped.append(job_id)
    return QueueBulkResponse(
        action=body.action,
        requested=len(requested),
        affected=len(changed),
        skipped=skipped,
    )


@api_router.post("/v1/jobs/queue/bulk/retry", response_model=QueueBulkResponse)
async def bulk_retry_jobs(
    body: QueueBulkRequest,
    identity: Identity = Depends(require_active_device_license),
    db: Session = Depends(get_db),
) -> QueueBulkResponse:
    from app.quota import check_job_quota, increment_job_quota, release_job_quota

    manager = get_job_manager()
    requested = list(dict.fromkeys(body.job_ids))
    changed: list[str] = []
    skipped: list[str] = []
    for job_id in requested:
        check_job_quota(identity, db)
        try:
            record = await manager.retry_job_for(job_id, identity)
        except Exception:
            release_job_quota(identity)
            skipped.append(job_id)
            continue
        if record is None:
            release_job_quota(identity)
            skipped.append(job_id)
            continue
        increment_job_quota(identity, db)
        changed.append(job_id)
    return QueueBulkResponse(
        action="retry",
        requested=len(requested),
        affected=len(changed),
        skipped=skipped,
    )


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


@api_router.post("/v1/jobs/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: str,
    identity: Identity = Depends(require_active_device_license),
    db: Session = Depends(get_db),
) -> JobResponse:
    from app.quota import check_job_quota, increment_job_quota, release_job_quota

    check_job_quota(identity, db)
    try:
        record = await get_job_manager().retry_job_for(job_id, identity)
    except Exception as exc:  # noqa: BLE001
        release_job_quota(identity)
        raise HTTPException(status_code=500, detail="job retry failed") from exc
    if record is None:
        release_job_quota(identity)
        raise HTTPException(status_code=400, detail="只有失败或已取消任务可以重试")
    increment_job_quota(identity, db)
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


@api_router.get(
    "/v1/automation/hongguo-new",
    response_model=HongguoMonitorStatus,
)
async def get_hongguo_new_monitor(
    identity: Identity = Depends(require_identity),
) -> HongguoMonitorStatus:
    from app.automation import get_hongguo_monitor_service

    return await get_hongguo_monitor_service().get_status(identity)


@api_router.put(
    "/v1/automation/hongguo-new",
    response_model=HongguoMonitorStatus,
)
async def configure_hongguo_new_monitor(
    request: Request,
    body: HongguoMonitorConfig,
    identity: Identity = Depends(require_active_device_license),
    gateway: LicenseGateway = Depends(get_license_gateway),
) -> HongguoMonitorStatus:
    if identity.kind != "user" or identity.is_ops:
        raise HTTPException(
            status_code=403,
            detail="BACKGROUND_LICENSE_CONTEXT_REQUIRED",
        )
    if body.quality != "1080p":
        raise HTTPException(status_code=400, detail="红果自动下载当前仅支持可播放的 1080p")
    from app.automation import get_hongguo_monitor_service

    verified_device_id = str(getattr(request.state, "verified_device_id", "") or "")
    if not verified_device_id:
        raise HTTPException(
            status_code=403,
            detail="BACKGROUND_LICENSE_CONTEXT_REQUIRED",
        )
    try:
        return await get_hongguo_monitor_service(gateway).configure(
            identity,
            body,
            verified_device_id=verified_device_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=403, detail=sanitize_error_text(exc)) from exc


@api_router.post(
    "/v1/automation/hongguo-new/scan",
    response_model=HongguoMonitorStatus,
)
async def scan_hongguo_new_now(
    identity: Identity = Depends(require_active_device_license),
    gateway: LicenseGateway = Depends(get_license_gateway),
) -> HongguoMonitorStatus:
    from app.automation import get_hongguo_monitor_service

    return await get_hongguo_monitor_service(gateway).scan_now(identity)


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
    request: Request,
    identity: Identity = Depends(require_identity),
) -> FileOpenResponse:
    manager = get_job_manager()
    if not manager.can_access_file(file_id, identity):
        raise HTTPException(status_code=404, detail="指定文件或目录不存在")
    path = manager.resolve_file(file_id)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="指定文件或目录不存在")
    settings = get_settings()
    if not (
        bool(getattr(settings, "server_side_file_open", False))
        or bool(getattr(settings, "allow_server_file_open", False))
    ):
        raise HTTPException(status_code=403, detail="SERVER_FILE_OPEN_DISABLED_USE_DESKTOP_BRIDGE")
    from app.security_boot import is_loopback_host

    client_host = request.client.host if request.client else ""
    if not is_loopback_host(client_host):
        raise HTTPException(status_code=403, detail="SERVER_FILE_OPEN_LOOPBACK_ONLY")
    if body.action not in {"play", "folder"}:
        raise HTTPException(status_code=400, detail="unsupported file open action")

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





