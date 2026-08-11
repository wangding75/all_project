"""Atomic daily job-quota reservation and accounting."""

from __future__ import annotations

import threading
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth import Identity
from app.config import get_settings
from app.models_orm import UsageDaily


# RD is deliberately a single-worker service.  This process lock closes the
# check/create/increment race between concurrent requests while SQLite keeps
# the durable count.  The reservation is not persisted as usage until the job
# has actually been accepted.
_quota_lock = threading.RLock()
_reservations: dict[tuple[int, str], int] = {}


def _day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _key(identity: Identity, day: str) -> tuple[int, str] | None:
    return (int(identity.user_id), day) if identity.user_id is not None else None


def _bypassed(identity: Identity) -> bool:
    return identity.is_ops or identity.kind == "api_key"


def check_job_quota(identity: Identity, db: Session) -> None:
    """Reserve one daily slot or raise HTTP 429.

    The public function name is retained for existing callers.  A successful
    call must be paired with ``increment_job_quota`` or ``release_job_quota``.
    """

    if _bypassed(identity):
        return
    limit = int(get_settings().vip_jobs_per_day)
    if limit <= 0:
        return
    day = _day()
    key = _key(identity, day)
    with _quota_lock:
        usage = (
            db.query(UsageDaily)
            .filter(UsageDaily.user_id == identity.user_id, UsageDaily.day == day)
            .first()
        )
        used = int(usage.job_count if usage else 0)
        pending = _reservations.get(key, 0) if key else 0
        if used + pending >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="今日下载配额已用尽",
            )
        if key:
            _reservations[key] = pending + 1


def increment_job_quota(identity: Identity, db: Session) -> None:
    """Commit a previously reserved slot to the durable daily count."""

    if _bypassed(identity):
        return
    day = _day()
    key = _key(identity, day)
    with _quota_lock:
        if key:
            pending = _reservations.get(key, 0)
            if pending <= 1:
                _reservations.pop(key, None)
            else:
                _reservations[key] = pending - 1
        usage = (
            db.query(UsageDaily)
            .filter(UsageDaily.user_id == identity.user_id, UsageDaily.day == day)
            .first()
        )
        if usage is None:
            db.add(UsageDaily(user_id=identity.user_id, day=day, job_count=1))
        else:
            usage.job_count += 1
        db.commit()


def release_job_quota(identity: Identity) -> None:
    """Release a reservation when the subsequent job creation fails."""

    if _bypassed(identity) or identity.user_id is None:
        return
    key = _key(identity, _day())
    if key is None:
        return
    with _quota_lock:
        pending = _reservations.get(key, 0)
        if pending <= 1:
            _reservations.pop(key, None)
        else:
            _reservations[key] = pending - 1
