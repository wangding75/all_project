"""SQLAlchemy 数据库模型。"""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.db import Base


class User(Base):
    """用户表模型。"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    # Legacy/display compatibility only. New activation never writes this;
    # License Service is the production authorization truth.
    vip_expires_at = Column(DateTime, nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CardKey(Base):
    """Legacy local CardKey data; not a current License Service truth source."""

    __tablename__ = "card_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(128), unique=True, nullable=False, index=True)
    duration_days = Column(Integer, nullable=False, default=30)
    batch_id = Column(String(64), nullable=True)
    is_used = Column(Boolean, nullable=False, default=False)
    used_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class UsageDaily(Base):
    """每日配额使用表模型。"""

    __tablename__ = "usage_daily"

    user_id = Column(Integer, primary_key=True)
    day = Column(String(10), primary_key=True)  # UTC YYYY-MM-DD
    job_count = Column(Integer, nullable=False, default=0)


class LicenseUsageDaily(Base):
    """Daily job usage keyed by the License Service subject."""

    __tablename__ = "license_usage_daily"

    license_id = Column(String(128), primary_key=True)
    day = Column(String(10), primary_key=True)  # UTC YYYY-MM-DD
    used_count = Column(Integer, nullable=False, default=0)
    limit_snapshot = Column(Integer, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class IdempotencyRecord(Base):
    """Durable, bounded replay record for License-subject Job creation."""

    __tablename__ = "idempotency_records"

    scope = Column(String(256), primary_key=True)
    key = Column(String(128), primary_key=True)
    fingerprint = Column(String(64), nullable=False)
    response_json = Column(Text, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    expires_at = Column(DateTime, nullable=False, index=True)
