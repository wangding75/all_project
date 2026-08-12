"""HTTP 路由。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse

from app import __version__
from app.auth import Identity, require_identity
from app.errors import format_platform_error, sanitize_error_text
from app.config import get_settings
from app.idempotency import (
    IdempotencyConflict,
    IdempotencyInProgress,
    idempotency_store,
    request_fingerprint,
)
from app.license_guard import require_active_device_license
from app.license_gateway import LicenseGateway, get_license_gateway
from app.download_resolution import normalize_platform_resolution, proxy_ticket_store
from app.models import (
    BatchResolveErrorItem,
    BatchResolveRequest,
    BatchResolveResponse,
    BatchResolvedItem,
    DetailResponse,
    DownloadResolveRequest,
    DownloadResolveResponse,
    HealthDependencyItem,
    HealthResponse,
    ImageRecognizeRequest,
    ImageRecognizeResponse,
    PeopleResponse,
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


def _activation_response(result: dict[str, Any]) -> RedeemResponse:
    decision = str(result.get("decision") or "UNKNOWN")
    reason = str(result.get("reason") or "")
    if decision == "UNKNOWN":
        if reason not in {
            "LICENSE_SERVICE_UNAVAILABLE",
            "LICENSE_SERVICE_TIMEOUT",
            "LICENSE_SERVICE_REJECTED",
        }:
            reason = "LICENSE_SERVICE_UNAVAILABLE"
        raise HTTPException(status_code=503, detail=reason)
    if decision != "ACTIVE":
        if reason == "INVALID_DEVICE_PROOF":
            reason = "DEVICE_PROOF_INVALID"
        raise HTTPException(status_code=403, detail=reason or "LICENSE_REQUIRED")
    return RedeemResponse(
        success=True,
        message=reason or "ACTIVATED",
        reason=reason or "ACTIVATED",
        license_expires_at=str(result["expires_at"]) if result.get("expires_at") is not None else None,
        max_devices=result.get("max_devices"),
        active_devices=result.get("active_devices"),
        license_id=result.get("license_id"),
        device_id=result.get("device_id"),
        plan_code=result.get("plan_code") or (result.get("plan") or {}).get("code"),
        plan_version=result.get("plan_version") or (result.get("plan") or {}).get("version"),
        entitlement_schema_version=result.get("entitlement_schema_version"),
        entitlements=dict(result.get("entitlements") or {}),
    )


@api_router.post("/v1/license/activate", response_model=RedeemResponse)
def activate_license(
    request: Request,
    body: RedeemRequest,
    gateway: LicenseGateway = Depends(get_license_gateway),
) -> RedeemResponse:
    """Activation-first Desktop entry point; no User/JWT is required."""
    card_code = body.card_code.strip()
    if not card_code:
        raise HTTPException(status_code=400, detail="INVALID_KEY")
    proof = body.proof
    if (
        not body.device_id
        or not body.device_key_algorithm
        or not body.device_public_key
        or proof is None
        or proof.timestamp is None
        or not proof.nonce
        or not proof.signature
    ):
        raise HTTPException(status_code=403, detail="DEVICE_PROOF_REQUIRED")
    result = gateway.activate(
        {
            "license_key": card_code,
            "device_id": body.device_id,
            "device_key_algorithm": body.device_key_algorithm,
            "device_public_key": body.device_public_key,
            "proof": {
                "timestamp": proof.timestamp,
                "nonce": proof.nonce,
                "signature": proof.signature,
            },
        },
        request_id=request.headers.get("X-Request-ID", ""),
    )
    return _activation_response(result)


@api_router.get("/v1/license/status")
async def license_status(
    request: Request,
    identity: Identity = Depends(require_active_device_license),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return the verified License Context and RD-owned daily usage."""
    from app.quota import get_license_usage

    result = dict(getattr(request.state, "license_result", {}) or {})
    usage = get_license_usage(identity, db)
    plan = result.get("plan") or {}
    return {
        "status": "ACTIVE",
        "reason": result.get("reason") or "ACTIVE",
        "license_id": identity.license_id,
        "device_id": identity.device_id,
        "plan_code": identity.plan_code or plan.get("code"),
        "plan_version": identity.plan_version or plan.get("version"),
        "entitlement_schema_version": identity.entitlement_schema_version,
        "entitlements": dict(identity.entitlements),
        "expires_at": result.get("expires_at"),
        **usage,
    }


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
    _: Identity = Depends(require_active_device_license),
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
    platform_status: dict[str, str] = {}
    for p, (plist, err) in zip(targets, results):
        if err:
            errors[p.value] = err
            platform_status[p.value] = (
                "RUNTIME_INCOMPATIBLE"
                if "RUNTIME_INCOMPATIBLE" in err
                else "UPSTREAM_UNAVAILABLE"
            )
        else:
            platform_status[p.value] = "OK" if plist else "EMPTY_RESULT"
        items.extend(plist)

    # 搜索结果始终返回 200；调用方根据 platform_status 区分空结果、上游不可用和运行时不兼容。
    return SearchResponse(
        items=items,
        platforms_queried=[p.value for p in targets],
        platform_errors=errors,
        platform_status=platform_status,
        total=len(items),
        page=page,
        page_size=20,
        has_more=any(len(platform_items) >= 20 for platform_items, _error in results),
    )


@api_router.post("/v1/batch/resolve", response_model=BatchResolveResponse)
async def resolve_batch(
    body: BatchResolveRequest,
    _: Identity = Depends(require_active_device_license),
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
    _: Identity = Depends(require_active_device_license),
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
    _: Identity = Depends(require_active_device_license),
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
    _: Identity = Depends(require_active_device_license),
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
    _: Identity = Depends(require_active_device_license),
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


def _idempotency_scope(identity: Identity) -> str:
    if identity.license_id and identity.device_id:
        return f"license:{identity.license_id}:device:{identity.device_id}"
    if identity.kind == "user" and identity.user_id is not None:
        return f"user:{identity.user_id}"
    return "ops"


def _read_idempotency_key(request: Request) -> str:
    key = (request.headers.get("Idempotency-Key") or "").strip()
    if len(key) > 128:
        raise HTTPException(status_code=400, detail="Idempotency-Key is too long")
    return key


@api_router.post("/v1/resolve", response_model=DownloadResolveResponse)
async def resolve_download(
    body: DownloadResolveRequest,
    request: Request,
    identity: Identity = Depends(require_active_device_license),
    db: Session = Depends(get_db),
) -> DownloadResolveResponse:
    """Authorize and resolve one client-owned download without server storage."""
    try:
        platform = get_platform(body.platform)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=sanitize_error_text(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=sanitize_error_text(exc)) from exc

    idempotency_key = _read_idempotency_key(request)
    idempotency_entry = None
    scope = _idempotency_scope(identity)
    fingerprint = request_fingerprint(body.model_dump(mode="json"))
    if idempotency_key:
        try:
            leader, idempotency_entry = idempotency_store.begin(
                scope,
                idempotency_key,
                fingerprint,
                db=db,
            )
        except IdempotencyConflict as exc:
            raise HTTPException(status_code=409, detail="IDEMPOTENCY_CONFLICT") from exc
        if not leader:
            import asyncio

            try:
                cached = await asyncio.to_thread(idempotency_store.wait, idempotency_entry)
            except IdempotencyInProgress as exc:
                raise HTTPException(status_code=409, detail="IDEMPOTENCY_IN_PROGRESS") from exc
            if cached is None:
                raise HTTPException(status_code=409, detail="IDEMPOTENCY_IN_PROGRESS")
            return DownloadResolveResponse.model_validate(cached).model_copy(update={"idempotent_replay": True})

    from app.quota import check_job_quota, get_license_usage, increment_job_quota, release_job_quota

    reserved = False
    try:
        check_job_quota(identity, db)
        reserved = True
        resolved = await platform.resolve_download(
            body.resource_id,
            title=body.title,
            range_spec=body.range,
            options=body.options,
        )
        descriptors = await normalize_platform_resolution(
            platform=body.platform,
            resource_id=body.resource_id,
            title=body.title,
            media_type=body.media_type,
            suggested_filename=body.suggested_filename,
            range_spec=body.range,
            options=body.options,
            resolved=resolved,
        )
        increment_job_quota(identity, db)
        reserved = False
        response = DownloadResolveResponse(
            descriptor=descriptors[0],
            descriptors=descriptors,
            quota=get_license_usage(identity, db),
        )
        if idempotency_key and idempotency_entry is not None:
            idempotency_store.complete(scope, idempotency_key, idempotency_entry, response.model_dump(mode="json"), db=db)
        return response
    except HTTPException:
        if reserved:
            release_job_quota(identity)
        if idempotency_key and idempotency_entry is not None:
            idempotency_store.fail(scope, idempotency_key, idempotency_entry, db=db)
        raise
    except NotImplementedError as exc:
        if reserved:
            release_job_quota(identity)
        if idempotency_key and idempotency_entry is not None:
            idempotency_store.fail(scope, idempotency_key, idempotency_entry, db=db)
        raise HTTPException(status_code=501, detail=sanitize_error_text(exc)) from exc
    except ValueError as exc:
        if reserved:
            release_job_quota(identity)
        if idempotency_key and idempotency_entry is not None:
            idempotency_store.fail(scope, idempotency_key, idempotency_entry, db=db)
        raise HTTPException(status_code=422, detail=sanitize_error_text(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        if reserved:
            release_job_quota(identity)
        if idempotency_key and idempotency_entry is not None:
            idempotency_store.fail(scope, idempotency_key, idempotency_entry, db=db)
        raise HTTPException(status_code=502, detail=f"download resolve failed: {format_platform_error(exc)}") from exc


@api_router.get("/v1/downloads/proxy/{token}")
async def stream_download_proxy(
    token: str,
    request: Request,
    _: Identity = Depends(require_active_device_license),
):
    """Stream a platform response; this route never writes server download files."""
    ticket = proxy_ticket_store.get(token)
    if ticket is None:
        raise HTTPException(status_code=404, detail="DOWNLOAD_TICKET_EXPIRED")

    import httpx

    if ticket.upstream_url:
        forwarded = {
            key: value
            for key, value in ticket.upstream_headers.items()
            if key.lower() not in {"host", "content-length", "cookie", "authorization"}
        }
        range_header = request.headers.get("range")
        if range_header:
            forwarded["Range"] = range_header

        async def _upstream():
            async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
                async with client.stream("GET", ticket.upstream_url, headers=forwarded) as response:
                    if response.status_code >= 400:
                        raise HTTPException(status_code=502, detail="UPSTREAM_DOWNLOAD_UNAVAILABLE")
                    async for chunk in response.aiter_bytes(1024 * 1024):
                        yield chunk

        return StreamingResponse(_upstream(), media_type="application/octet-stream")

    try:
        platform = get_platform(ticket.platform)
        content = platform.stream_download(
            ticket.resource_id,
            range_spec=ticket.range_spec,
            options=ticket.options,
        )
    except (KeyError, NotImplementedError) as exc:
        raise HTTPException(status_code=501, detail=sanitize_error_text(exc)) from exc
    return StreamingResponse(content, media_type="application/octet-stream")


@api_router.get("/v1/admin/sign-pool")
async def admin_sign_pool(
    identity: Identity = Depends(require_identity),
) -> dict[str, Any]:
    if not identity.is_ops:
        raise HTTPException(status_code=403, detail="仅 API Key 运维权限可访问此接口")
    from app.sign_pool import get_sign_pool

    return get_sign_pool().get_summary()





