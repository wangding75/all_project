"""用户认证 API 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
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
from app.models_orm import User
from app.schemas_auth import (
    UserLoginRequest,
    UserLoginResponse,
    UserMeResponse,
    UserRegisterRequest,
    UserRegisterResponse,
)

auth_router = APIRouter()


@auth_router.post(
    "/v1/auth/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
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
