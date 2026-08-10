"""管理员与运维 API 路由。"""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import shutil
from sqlalchemy import text
from app.auth import Identity, require_ops
from app.config import get_settings
from app.db import get_db
from app.jobs import get_job_manager
from app.license_gateway import get_license_gateway
from app.logger import metrics_tracker
from app.models_orm import CardKey, UsageDaily, User
from app.schemas_admin import (
    AdminHealthResponse,
    AdminMetricsResponse,
    BatchInvalidateRequest,
    BatchInvalidateResponse,
    UserDetailResponse,
    UserListItem,
    UserListResponse,
    UserStatusUpdateRequest,
    UserStatusUpdateResponse,
)

admin_router = APIRouter(prefix="/v1/admin", dependencies=[Depends(require_ops)])


@admin_router.post(
    "/users/{user_id}/status",
    response_model=UserStatusUpdateResponse,
)
def update_user_status(
    user_id: int,
    body: UserStatusUpdateRequest,
    db: Session = Depends(get_db),
) -> UserStatusUpdateResponse:
    """更新用户状态（启用/禁用）。"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    user.is_active = body.is_active
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    return UserStatusUpdateResponse.model_validate(user)


@admin_router.post(
    "/card-keys/invalidate-batch",
    response_model=BatchInvalidateResponse,
)
def invalidate_card_key_batch(
    body: BatchInvalidateRequest,
    db: Session = Depends(get_db),
) -> BatchInvalidateResponse:
    """仅维护历史 RD CardKey 数据；不会 revoke License Service License。"""
    # 查找属于该批次且未被使用的卡密
    query = db.query(CardKey).filter(
        CardKey.batch_id == body.batch_id,
        CardKey.is_used == False,
    )
    count = query.count()
    if count == 0:
        return BatchInvalidateResponse(
            batch_id=body.batch_id,
            invalidated_count=0,
        )

    # 标识为已被作废 (is_used=True，无使用用户表示作废)
    query.update({CardKey.is_used: True}, synchronize_session=False)
    db.commit()

    return BatchInvalidateResponse(
        batch_id=body.batch_id,
        invalidated_count=count,
    )


@admin_router.get(
    "/users/{user_id}",
    response_model=UserDetailResponse,
)
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
) -> UserDetailResponse:
    """查询指定用户的详细状态与数据指标。"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    is_vip = bool(user.vip_expires_at and user.vip_expires_at > now_utc)

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    usage = (
        db.query(UsageDaily)
        .filter(UsageDaily.user_id == user.id, UsageDaily.day == today_str)
        .first()
    )
    job_count_today = usage.job_count if usage else 0

    return UserDetailResponse(
        id=user.id,
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        vip_expires_at=user.vip_expires_at,
        is_vip=is_vip,
        job_count_today=job_count_today,
    )


@admin_router.get(
    "/users",
    response_model=UserListResponse,
)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> UserListResponse:
    """分页列表查询所有注册用户。"""
    total = db.query(User).count()
    users = db.query(User).order_by(User.id.asc()).offset(skip).limit(limit).all()

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    items = []
    for u in users:
        is_vip = bool(u.vip_expires_at and u.vip_expires_at > now_utc)
        items.append(
            UserListItem(
                id=u.id,
                username=u.username,
                is_active=u.is_active,
                created_at=u.created_at,
                vip_expires_at=u.vip_expires_at,
                is_vip=is_vip,
            )
        )

    return UserListResponse(total=total, users=items)


@admin_router.get(
    "/health",
    response_model=AdminHealthResponse,
)
def admin_health(
    db: Session = Depends(get_db),
) -> AdminHealthResponse:
    """深度检查底层 SQLite、磁盘空间与签名池探活状态。"""
    # 1. 检查数据库连通性
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    # 2. 检查存储空间
    settings = get_settings()
    disk_free_bytes = 0
    disk_free_human = "0 B"
    try:
        usage = shutil.disk_usage(settings.outputs_dir)
        disk_free_bytes = usage.free
        if disk_free_bytes >= 1024**3:
            disk_free_human = f"{disk_free_bytes / (1024**3):.2f} GB"
        elif disk_free_bytes >= 1024**2:
            disk_free_human = f"{disk_free_bytes / (1024**2):.2f} MB"
        else:
            disk_free_human = f"{disk_free_bytes / 1024:.2f} KB"
    except Exception:
        pass

    # 3. 统计当前活跃 Job
    manager = get_job_manager()
    active_jobs = len([j for j in manager._jobs.values() if j.status.value in ("pending", "running")])

    # 4. 签名池状态摘要
    sign_pool_summary = {"enabled": settings.sign_pool_enabled}
    if settings.sign_pool_enabled:
        try:
            from app.sign_pool import get_sign_pool
            pool = get_sign_pool()
            sign_pool_summary.update(pool.summary())
        except Exception as e:
            sign_pool_summary["error"] = str(e)

    overall_status = "ok" if db_status == "ok" else "degraded"
    license_health = get_license_gateway().health()

    return AdminHealthResponse(
        status=overall_status,
        db_status=db_status,
        disk_free_human=disk_free_human,
        disk_free_bytes=disk_free_bytes,
        active_jobs=active_jobs,
        sign_pool_summary=sign_pool_summary,
        **license_health,
    )


@admin_router.get(
    "/metrics",
    response_model=AdminMetricsResponse,
)
def admin_metrics() -> AdminMetricsResponse:
    """获取进程内运行指标统计。"""
    summary = metrics_tracker.get_summary()
    return AdminMetricsResponse.model_validate(summary)
