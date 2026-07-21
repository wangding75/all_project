"""用户认证与卡密兑换 API 路由。"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
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
from app.models import RedeemRequest, RedeemResponse
from app.models_orm import User, CardKey
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
) -> User:
    """获取当前登录用户信息。"""
    # 仅 Key 时返回 400，明确非用户身份
    if identity.kind == "api_key" or identity.is_ops:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="非用户身份",
        )

    # 查询用户信息
    user = db.query(User).filter(User.id == identity.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    return user


@auth_router.post(
    "/v1/auth/redeem",
    response_model=RedeemResponse,
)
def redeem_card(
    body: RedeemRequest,
    identity: Identity = Depends(require_identity),
    db: Session = Depends(get_db),
) -> RedeemResponse:
    """卡密兑换以延长 VIP 有效期（事务安全）。"""
    # ops/api_key 兑换返回 400 或 403 明确非用户身份限制
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

    now_utc = datetime.now(timezone.utc)
    # SQLite naive datetime matching
    now_naive = now_utc.replace(tzinfo=None)

    # 用 UPDATE ... WHERE code = ? AND is_used = 0 做原子性/行锁校验
    stmt = (
        update(CardKey)
        .where(CardKey.code == card_code)
        .where(CardKey.is_used == False)
        .values(
            is_used=True,
            used_by_user_id=identity.user_id,
            used_at=now_naive,
        )
    )

    try:
        result = db.execute(stmt)
        if result.rowcount == 0:
            # 校验到底是卡密不存在，还是卡密已被使用
            card = db.query(CardKey).filter(CardKey.code == card_code).first()
            if not card:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="卡密不存在",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="卡密已被使用",
                )

        # 获取刚标记使用的 card
        card = db.query(CardKey).filter(CardKey.code == card_code).first()
        # 获取用户
        user = db.query(User).filter(User.id == identity.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户不存在",
            )

        # VIP 延期计算：base = max(now, user.vip_expires_at or now)
        base_time = now_naive
        if user.vip_expires_at and user.vip_expires_at > now_naive:
            base_time = user.vip_expires_at

        new_vip_expires_at = base_time + timedelta(days=card.duration_days)
        user.vip_expires_at = new_vip_expires_at

        db.commit()

        # 对齐 RedeemResponse
        return RedeemResponse(
            success=True,
            message="卡密兑换成功",
            vip_expires_at=new_vip_expires_at.isoformat(),
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"卡密兑换失败: {exc}",
        ) from exc
