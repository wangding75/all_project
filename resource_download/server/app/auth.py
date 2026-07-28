"""身份鉴权与密码/JWT 工具。"""

from __future__ import annotations

import logging
import jwt
import bcrypt
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models_orm import User

logger = logging.getLogger(__name__)


class Identity(BaseModel):
    """请求身份：运维 API Key 或登录用户。"""

    kind: str = Field(description='api_key | user')
    user_id: int | None = None
    username: str | None = None
    is_ops: bool = False


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _match_api_key(x_api_key: str | None) -> Identity | None:
    settings = get_settings()
    if x_api_key and x_api_key == settings.api_key:
        return Identity(kind="api_key", is_ops=True)
    return None


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


# --- 密码 Hash (bcrypt) ---

def hash_password(password: str) -> str:
    """使用 bcrypt 加密密码。"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """校验 bcrypt 密码。"""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# --- JWT 签发与校验 ---

def create_access_token(user_id: int, username: str) -> str:
    """生成 JWT 访问令牌。"""
    from datetime import datetime, timezone, timedelta
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_jwt(token: str) -> dict:
    """解析 JWT 令牌。"""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


# --- 身份校验依赖注入 ---

async def require_identity(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> Identity:
    """统一身份依赖：根据 AUTH_MODE 校验 API Key 和/或 Bearer JWT。"""
    settings = get_settings()
    mode = (settings.auth_mode or "dev").strip().lower()
    if mode not in {"dev", "dual", "jwt_only"}:
        logger.error("非法 AUTH_MODE=%r，拒绝降级到开发模式", mode)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务端鉴权模式配置错误",
        )

    if mode == "dev":
        # dev 模式：仅校验 X-API-Key，忽略 Bearer
        identity = _match_api_key(x_api_key)
        if identity is None:
            raise _unauthorized("Invalid or missing X-API-Key")
        return identity

    if mode == "dual":
        # dual 模式：① Key 匹配 -> ops 身份；② 否则校验 Bearer
        identity = _match_api_key(x_api_key)
        if identity is not None:
            return identity

        token = _bearer_token(authorization)
        if token is not None:
            try:
                payload = decode_jwt(token)
                user_id_str = payload.get("sub")
                if not user_id_str:
                    raise _unauthorized("Invalid or expired token")
                user_id = int(user_id_str)
                # 查库校验用户存在且活跃
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.is_active:
                    raise _unauthorized("Invalid or expired token")
                return Identity(
                    kind="user",
                    user_id=user.id,
                    username=user.username,
                    is_ops=False,
                )
            except (jwt.PyJWTError, ValueError):
                raise _unauthorized("Invalid or expired token")

        raise _unauthorized("Invalid or missing X-API-Key or Authorization Bearer token")

    # jwt_only 模式：仅校验 Bearer JWT
    token = _bearer_token(authorization)
    if token is None:
        raise _unauthorized("Missing or invalid Authorization Bearer token")

    try:
        payload = decode_jwt(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise _unauthorized("Invalid or expired token")
        user_id = int(user_id_str)
        # 查库校验用户
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise _unauthorized("Invalid or expired token")
        return Identity(
            kind="user",
            user_id=user.id,
            username=user.username,
            is_ops=False,
        )
    except (jwt.PyJWTError, ValueError):
        raise _unauthorized("Invalid or expired token")


async def require_api_key(
    identity: Identity = Depends(require_identity),
) -> Identity:
    """兼容旧依赖名；内部走 require_identity。"""
    return identity


async def require_ops(
    identity: Identity = Depends(require_identity),
) -> Identity:
    """校验请求身份必须具有 ops 运维管理权限。"""
    if identity.is_ops or identity.kind == "api_key":
        return identity
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="需要运维管理员权限 (ops API Key)",
    )



async def require_vip(
    identity: Identity = Depends(require_identity),
    db: Session = Depends(get_db),
) -> Identity:
    """校验是否是 VIP 或者是 ops API Key 身份。"""
    if identity.is_ops or identity.kind == "api_key":
        return identity

    if identity.kind == "user" and identity.user_id is not None:
        user = db.query(User).filter(User.id == identity.user_id).first()
        if user and user.is_active:
            from datetime import datetime, timezone
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            if user.vip_expires_at and user.vip_expires_at > now_utc:
                return identity

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="需要 VIP，请兑换卡密",
    )
