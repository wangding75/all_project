"""Atomic daily job-quota reservation and accounting."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth import Identity
from app.config import get_settings
from app.models_orm import LicenseUsageDaily, UsageDaily


_quota_lock = threading.RLock()
_reservations: dict[tuple[str, str], int] = {}


def _day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _license_key(identity: Identity, day: str) -> tuple[str, str] | None:
    if identity.license_id:
        return (str(identity.license_id), day)
    if identity.user_id is not None:
        return (f"legacy:user:{identity.user_id}", day)
    return None


def _bypassed(identity: Identity) -> bool:
    return identity.is_ops or identity.kind == "api_key"


def _entitlement_limit(identity: Identity) -> int:
    """Return the only quota value RD is allowed to enforce."""
    if identity.license_id:
        raw = identity.entitlements.get("quota.daily_jobs")
        if isinstance(raw, bool) or not isinstance(raw, int) or raw <= 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="PLAN_ENTITLEMENT_INVALID",
            )
        return raw
    # Compatibility for direct legacy unit callers.  Requests entering the
    # protected job API receive a context from license_guard first.
    return int(get_settings().vip_jobs_per_day)


def _legacy_usage(identity: Identity, db: Session, day: str) -> UsageDaily | None:
    if identity.license_context_source == "legacy_compat" and identity.user_id is not None:
        return (
            db.query(UsageDaily)
            .filter(UsageDaily.user_id == identity.user_id, UsageDaily.day == day)
            .first()
        )
    return None


def check_job_quota(identity: Identity, db: Session) -> None:
    """Reserve one daily slot or raise HTTP 429.

    A License Service context makes ``license_id`` the subject.  The legacy
    User table is only mirrored for old local displays and compatibility tests.
    """
    if _bypassed(identity):
        return
    limit = _entitlement_limit(identity)
    if limit <= 0:
        return
    day = _day()
    key = _license_key(identity, day)
    with _quota_lock:
        usage = None
        if identity.license_id:
            usage = (
                db.query(LicenseUsageDaily)
                .filter(
                    LicenseUsageDaily.license_id == identity.license_id,
                    LicenseUsageDaily.day == day,
                )
                .first()
            )
        else:
            usage = _legacy_usage(identity, db, day)
        used = int((usage.used_count if identity.license_id else usage.job_count) if usage else 0)
        effective_limit = int(usage.limit_snapshot) if identity.license_id and usage else limit
        pending = _reservations.get(key, 0) if key else 0
        if used + pending >= effective_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="\u4eca\u65e5\u4e0b\u8f7d\u914d\u989d\u5df2\u7528\u5c3d",
            )
        if key:
            _reservations[key] = pending + 1


def increment_job_quota(identity: Identity, db: Session) -> None:
    """Commit a previously reserved slot to durable License usage."""
    if _bypassed(identity):
        return
    limit = _entitlement_limit(identity)
    day = _day()
    key = _license_key(identity, day)
    with _quota_lock:
        if key:
            pending = _reservations.get(key, 0)
            if pending <= 1:
                _reservations.pop(key, None)
            else:
                _reservations[key] = pending - 1
        if identity.license_id:
            usage = (
                db.query(LicenseUsageDaily)
                .filter(
                    LicenseUsageDaily.license_id == identity.license_id,
                    LicenseUsageDaily.day == day,
                )
                .first()
            )
            if usage is None:
                db.add(
                    LicenseUsageDaily(
                        license_id=identity.license_id,
                        day=day,
                        used_count=1,
                        limit_snapshot=limit,
                    )
                )
            else:
                usage.used_count += 1
                usage.limit_snapshot = min(int(usage.limit_snapshot), limit)
            if identity.license_context_source == "legacy_compat" and identity.user_id is not None:
                legacy = _legacy_usage(identity, db, day)
                if legacy is None:
                    db.add(UsageDaily(user_id=identity.user_id, day=day, job_count=1))
                else:
                    legacy.job_count += 1
        else:
            usage = _legacy_usage(identity, db, day)
            if usage is None and identity.user_id is not None:
                db.add(UsageDaily(user_id=identity.user_id, day=day, job_count=1))
            elif usage is not None:
                usage.job_count += 1
        db.commit()


def release_job_quota(identity: Identity) -> None:
    """Release a reservation when the subsequent job creation fails."""
    if _bypassed(identity):
        return
    key = _license_key(identity, _day())
    if key is None:
        return
    with _quota_lock:
        pending = _reservations.get(key, 0)
        if pending <= 1:
            _reservations.pop(key, None)
        else:
            _reservations[key] = pending - 1


def get_license_usage(identity: Identity, db: Session) -> dict[str, Any]:
    """Return the current License subject usage for status/statistics UI."""
    if not identity.license_id:
        return {"used": 0, "limit": int(get_settings().vip_jobs_per_day), "day": _day()}
    day = _day()
    usage = (
        db.query(LicenseUsageDaily)
        .filter(
            LicenseUsageDaily.license_id == identity.license_id,
            LicenseUsageDaily.day == day,
        )
        .first()
    )
    limit = _entitlement_limit(identity)
    return {
        "license_id": identity.license_id,
        "day": day,
        "used": int(usage.used_count if usage else 0),
        "limit": int(usage.limit_snapshot if usage else limit),
    }
