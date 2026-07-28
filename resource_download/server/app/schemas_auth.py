"""认证与用户 Pydantic DTO。"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRegisterRequest(BaseModel):
    """用户注册请求参数。"""

    username: str = Field(
        ...,
        min_length=3,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="用户名，3-64位字母数字或下划线",
    )
    password: str = Field(..., description="密码，长度至少 8 位，最多 72 字节")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 bytes")
        return v


class UserRegisterResponse(BaseModel):
    """用户注册响应数据（用户摘要，无密码）。"""

    id: int
    username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    vip_expires_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserLoginRequest(BaseModel):
    """用户登录请求参数。"""

    username: str
    password: str


class UserLoginResponse(BaseModel):
    """用户登录成功后的 token 响应。"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    vip_expires_at: datetime | None


class UserMeResponse(BaseModel):
    """用户个人信息（GET /v1/auth/me 响应）。"""

    id: int
    username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    vip_expires_at: datetime | None
    # 额度展示（设置页）
    is_vip: bool = False
    jobs_today: int = 0
    jobs_limit: int = 0

    model_config = ConfigDict(from_attributes=True)
