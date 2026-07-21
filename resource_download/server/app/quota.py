"""每日建任务配额校验层。"""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth import Identity
from app.config import get_settings
from app.models_orm import UsageDaily


def check_job_quota(identity: Identity, db: Session) -> None:
    """在创建任务前校验用户的每日配额限制。"""
    # ops 角色 / API Key 豁免限制
    if identity.is_ops or identity.kind == "api_key":
        return

    settings = get_settings()
    limit = settings.vip_jobs_per_day

    # 限制为 0 时表示不限日次数
    if limit <= 0:
        return

    # 全流程 UTC 时间日历日
    day_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 查询今日已建任务数
    usage = (
        db.query(UsageDaily)
        .filter(UsageDaily.user_id == identity.user_id, UsageDaily.day == day_str)
        .first()
    )
    count = usage.job_count if usage else 0

    if count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="今日下载配额已用尽",
        )


def increment_job_quota(identity: Identity, db: Session) -> None:
    """任务创建成功后累加用户每日配额计数。"""
    # ops 角色 / API Key 豁免
    if identity.is_ops or identity.kind == "api_key":
        return

    # 全流程 UTC 时间日历日
    day_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 查询今日记录
    usage = (
        db.query(UsageDaily)
        .filter(UsageDaily.user_id == identity.user_id, UsageDaily.day == day_str)
        .first()
    )

    if not usage:
        usage = UsageDaily(
            user_id=identity.user_id,
            day=day_str,
            job_count=1,
        )
        db.add(usage)
    else:
        usage.job_count += 1

    db.commit()
