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




@api_router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """配置 + 设备运行时完整性检查（只探测不自启）。"""
    extra_platforms = list_platforms()
    runtime_report: dict | None = None
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

    report = build_health_report(include_runtime=True, runtime_report=runtime_report)
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


@api_router.get("/v1/version", response_model=VersionResponse)
async def get_version() -> VersionResponse:
    """获取应用权威当前版本及更新检视状态。"""
    return VersionResponse(
        version=__version__,
        update_check_enabled=False,
        latest_version=__version__,
        has_update=False,
        download_url="",
        release_notes="ResourceDownloader 统一版本描述。",
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
    )


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
    _: Identity = Depends(require_identity),
) -> DiscoverResponse:
    """首页发现页：热榜 / 今日上新。

    当前为 **契约就绪 + stub**：App 内榜单/上新协议尚未接入平台适配层。
    客户端可先渲染空态与 UI；接入后仅改服务端，响应形状保持不变。
    """
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

    sections: list[DiscoverSection] = []
    for kind in kind_list:
        if kind not in title_map:
            continue
        # 预留：未来在 platforms.*.discover_hot / discover_new 拉取后填充 items
        sections.append(
            DiscoverSection(
                kind=kind,
                title=title_map[kind],
                items=[],  # type: ignore[arg-type]
                available=False,
                message=(
                    f"{plat_hint} · {title_map[kind]} 数据待接入服务端平台协议"
                    "（Frida/App 榜单接口）。可先用「资源搜索」按关键词查找。"
                ),
                platform_errors={},
            )
        )

    return DiscoverResponse(
        sections=sections,
        platforms_queried=[p.value for p in targets],
        data_mode="stub",
        note=f"当前平台：{plat_hint}。榜单/上新 API 契约已就绪；真实数据待 platforms 适配层接入。",
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
            res.extra["qualities"] = ["1080p", "720p"]

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





