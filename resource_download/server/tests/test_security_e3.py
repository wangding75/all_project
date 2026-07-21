"""阶段 E3 — 生产安全默认启动校验单元测试。"""

from __future__ import annotations

import pytest
from app.config import Settings
from app.security_boot import assert_production_secrets, is_loopback_host, mask_secret


def test_is_loopback_host():
    assert is_loopback_host("127.0.0.1") is True
    assert is_loopback_host("localhost") is True
    assert is_loopback_host("::1") is True
    assert is_loopback_host("0.0.0.0") is False
    assert is_loopback_host("192.168.1.10") is False


def test_mask_secret():
    assert mask_secret("1234567890") == "1234***7890"
    assert mask_secret("short") == "***"
    assert mask_secret("") == ""


def test_dual_mode_default_jwt_secret_rejected():
    """AUTH_MODE=dual 且使用默认 JWT_SECRET 时必须拒绝启动。"""
    settings = Settings(
        auth_mode="dual",
        jwt_secret="change-me-jwt-secret",
        api_key="strong-key-12345678",
        host="127.0.0.1",
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET 仍为默认值"):
        assert_production_secrets(settings)


def test_jwt_only_mode_default_jwt_secret_rejected():
    """AUTH_MODE=jwt_only 且使用默认 JWT_SECRET 时必须拒绝启动。"""
    settings = Settings(
        auth_mode="jwt_only",
        jwt_secret="change-me-jwt-secret",
        api_key="strong-key-12345678",
        host="127.0.0.1",
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET 仍为默认值"):
        assert_production_secrets(settings)


def test_default_api_key_non_loopback_rejected():
    """API_KEY 为默认值且 HOST 非 loopback (如 0.0.0.0) 时必须拒绝启动。"""
    settings = Settings(
        auth_mode="dual",
        jwt_secret="super-strong-jwt-secret-key-32bytes!",
        api_key="dev-key-change-me",
        host="0.0.0.0",
    )
    with pytest.raises(RuntimeError, match="API_KEY 仍为默认开发 Key"):
        assert_production_secrets(settings)


def test_dual_mode_strong_secrets_public_host_allowed():
    """AUTH_MODE=dual，配合强 JWT 与强 API Key，且 HOST=0.0.0.0 时校验通过。"""
    settings = Settings(
        auth_mode="dual",
        jwt_secret="super-strong-jwt-secret-key-32bytes!",
        api_key="strong-api-key-99999999",
        host="0.0.0.0",
    )
    # 不应抛出任何异常
    assert_production_secrets(settings)


def test_dev_mode_default_key_localhost_allowed():
    """AUTH_MODE=dev，默认 API Key 且 HOST=127.0.0.1 时校验通过（允许开发旁路）。"""
    settings = Settings(
        auth_mode="dev",
        jwt_secret="change-me-jwt-secret",
        api_key="dev-key-change-me",
        host="127.0.0.1",
    )
    # 不应抛出任何异常
    assert_production_secrets(settings)
