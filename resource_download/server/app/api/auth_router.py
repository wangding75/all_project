"""用户认证与卡密兑换 API 路由。"""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import (
    Identity,
    create_access_token,
    hash_password,
    require_identity,
    verify_password,
)
from app.config import get_settings
from app.db import get_db
from app.license_gateway import LicenseGateway, get_license_gateway
from app.models import RedeemRequest, RedeemResponse
from app.models_orm import User
from app.schemas_auth import (
    UserLoginRequest,
    UserLoginResponse,
    UserMeResponse,
    UserRegisterRequest,
    UserRegisterResponse,
)
from app.rate_limit import ip_rate_limiter

auth_router = APIRouter()


@auth_router.post(
    "/v1/auth/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(ip_rate_limiter("auth"))],
)
def register(
    body: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> User:
    """注册新用户。"""
    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == body.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    # 创建用户
    hashed = hash_password(body.password)
    new_user = User(
        username=body.username,
        hashed_password=hashed,
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        ) from exc

    return new_user


@auth_router.post(
    "/v1/auth/login",
    response_model=UserLoginResponse,
    dependencies=[Depends(ip_rate_limiter("auth"))],
)
def login(
    body: UserLoginRequest,
    db: Session = Depends(get_db),
) -> UserLoginResponse:
    """用户登录校验，签发 JWT。"""
    # 查询用户
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # 检查用户是否启用
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用",
        )

    # 生成 Token
    settings = get_settings()
    token = create_access_token(user.id, user.username)

    return UserLoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60,
        vip_expires_at=user.vip_expires_at,
    )


@auth_router.get(
    "/v1/auth/me",
    response_model=UserMeResponse,
)
def me(
    identity: Identity = Depends(require_identity),
    db: Session = Depends(get_db),
) -> UserMeResponse:
    """获取当前登录用户信息（含今日额度）。"""
    from app.models_orm import UsageDaily

    # 仅 Key 时返回 400，明确非用户身份
    if identity.kind == "api_key" or identity.is_ops:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="非用户身份",
        )

    user = db.query(User).filter(User.id == identity.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    settings = get_settings()
    day_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    usage = (
        db.query(UsageDaily)
        .filter(UsageDaily.user_id == user.id, UsageDaily.day == day_str)
        .first()
    )
    jobs_today = usage.job_count if usage else 0
    jobs_limit = settings.vip_jobs_per_day
    is_vip = False
    if user.vip_expires_at is not None:
        exp = user.vip_expires_at
        if exp.tzinfo is None:
            is_vip = exp > datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            is_vip = exp > datetime.now(timezone.utc)

    return UserMeResponse(
        id=user.id,
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        vip_expires_at=user.vip_expires_at,
        is_vip=is_vip,
        jobs_today=jobs_today,
        jobs_limit=jobs_limit,
    )


@auth_router.post(
    "/v1/auth/redeem",
    response_model=RedeemResponse,
)
def redeem_card(
    request: Request,
    body: RedeemRequest,
    identity: Identity = Depends(require_identity),
    gateway: LicenseGateway = Depends(get_license_gateway),
) -> RedeemResponse:
    """Activation proxy: authenticate the RD user, then delegate to License Service.

    ``card_code`` is a compatibility field name only.  This endpoint does not
    read/write ``CardKey`` and does not update ``User.vip_expires_at``.
    """
    if identity.kind == "api_key" or identity.is_ops:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="请使用用户登录后兑换",
        )

    card_code = body.card_code.strip()
    if not card_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="卡密序列号不能为空",
        )

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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DEVICE_PROOF_REQUIRED",
        )

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
    decision = str(result.get("decision") or "UNKNOWN")
    reason = str(result.get("reason") or "")
    if decision == "UNKNOWN":
        if reason not in {
            "LICENSE_SERVICE_UNAVAILABLE",
            "LICENSE_SERVICE_TIMEOUT",
            "LICENSE_SERVICE_REJECTED",
        }:
            reason = "LICENSE_SERVICE_UNAVAILABLE"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=reason)
    if decision != "ACTIVE":
        if reason == "INVALID_DEVICE_PROOF":
            reason = "DEVICE_PROOF_INVALID"
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=reason or "LICENSE_REQUIRED")

    expires_at = result.get("expires_at")
    return RedeemResponse(
        success=True,
        message=reason or "ACTIVATED",
        reason=reason or "ACTIVATED",
        license_expires_at=str(expires_at) if expires_at is not None else None,
        vip_expires_at=str(expires_at) if expires_at is not None else None,
        max_devices=result.get("max_devices"),
        active_devices=result.get("active_devices"),
    )
