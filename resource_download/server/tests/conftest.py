"""pytest 全局测试配置与通用隔离夹具 (Stage CQ-02)。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock
import pytest

# 确保导入路径包含 server 目录
server_dir = Path(__file__).resolve().parent.parent / "server"
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))

from app.config import get_settings
from app.license_gateway import get_license_gateway
from app.main import app
from app.logger import metrics_tracker
from app.models import DetailResponse, PlatformName, SearchItem, SegmentInfo
from app.rate_limit import ip_rate_limiter
from app.rate_limit import _rate_limit_cache, _rate_limit_lock
from platforms.base import BasePlatform


class FakeLicenseGateway:
    """Deterministic License Service boundary for RD unit tests.

    Contract/HTTP E2E coverage uses the real SDK in dedicated tests below; the
    existing business tests inject this boundary so they can remain offline.
    """

    configured = True
    cache_ttl_seconds = 30

    def __init__(self):
        self.check_result = {
            "activated": True,
            "reason": "ACTIVE",
            "decision": "ACTIVE",
            "source": "remote",
            "device_public_key": "test-public-key",
            "device_key_algorithm": "ED25519",
        }
        self.activate_result = {
            "activated": True,
            "reason": "ACTIVATED",
            "decision": "ACTIVE",
            "source": "remote",
            "expires_at": "2099-01-01T00:00:00+00:00",
            "max_devices": 2,
            "active_devices": 1,
        }
        self.requests: list[dict] = []
        self.activations: list[dict] = []
        self.entitlement_requests: list[str] = []
        self.entitlement_result = {
            "activated": True,
            "reason": "ACTIVE",
            "decision": "ACTIVE",
            "source": "remote",
        }

    def authorize_request(self, **kwargs):
        self.requests.append(kwargs)
        return dict(self.check_result)

    def activate(self, payload, **_kwargs):
        self.activations.append(payload)
        return dict(self.activate_result)

    def check_device_entitlement(self, device_id, **_kwargs):
        self.entitlement_requests.append(device_id)
        return dict(self.entitlement_result)

    def health(self):
        return {
            "license_service_configured": True,
            "license_service_reachable": True,
            "license_cache_ttl_seconds": self.cache_ttl_seconds,
        }

    def close(self):
        return None


@pytest.fixture(autouse=True)
def license_gateway_for_tests():
    """Keep ordinary RD tests offline while preserving the real guard path."""
    gateway = FakeLicenseGateway()
    app.dependency_overrides[get_license_gateway] = lambda: gateway
    yield gateway
    app.dependency_overrides.pop(get_license_gateway, None)


@pytest.fixture
def device_headers():
    return {
        "X-Device-Id": "dev_" + "1" * 64,
        "X-Device-Key-Algorithm": "ED25519",
        "X-Device-Proof-Timestamp": "1760000000",
        "X-Device-Proof-Nonce": "test-proof-nonce-123456",
        "X-Device-Proof-Signature": "test-proof-signature",
    }


@pytest.fixture(autouse=True)
def clean_test_environment():
    """在每个测试前后自动隔离重置环境变量与设置缓存。"""
    original_environ = dict(os.environ)
    # 自动化测试必须完全离线、确定性运行；真实 ADB/Frida/平台联调单独执行。
    os.environ["PLATFORM_PROBE_ON_STARTUP"] = "false"
    os.environ["FANQIE_PROBE_ON_STARTUP"] = "false"
    os.environ["FANQIE_TRY_START_AGENT"] = "false"
    os.environ["TRY_START_PLATFORM_APPS"] = "false"
    os.environ["REQUIRE_PLATFORM_APPS"] = "false"
    os.environ["FANQIE_REQUIRE_RUNTIME"] = "false"
    # The application default is the production-safe dual auth mode.  Unit
    # tests still exercise that mode, so provide a non-default signing secret
    # instead of forcing AUTH_MODE=dev or relying on the caller's environment.
    os.environ["JWT_SECRET"] = "t35-pytest-jwt-secret-32-bytes-minimum"
    # Legacy User/JWT tests are explicit compatibility coverage.  Production
    # defaults to the License-only path via Settings.legacy_user_auth_enabled.
    os.environ["LEGACY_USER_AUTH_ENABLED"] = "true"
    get_settings.cache_clear()
    with _rate_limit_lock:
        _rate_limit_cache.clear()
    
    yield

    os.environ.clear()
    os.environ.update(original_environ)
    get_settings.cache_clear()
    with _rate_limit_lock:
        _rate_limit_cache.clear()


class FakeMockPlatform(BasePlatform):
    """测试专用的脱机虚构适配器 (完全脱离真实外部网络)。"""

    def __init__(self, name: str = "hongguo"):
        self.name = name

    async def search(self, query: str, page: int = 1) -> list[SearchItem]:
        return [
            SearchItem(
                id="mock_item_1",
                title=f"Mock 搜索结果 - {query}",
                cover="http://mock.local/cover.jpg",
                author="Mock作者",
                desc="Mock描述",
            )
        ]

    async def get_detail(self, item_id: str) -> DetailResponse:
        return DetailResponse(
            platform=PlatformName.hongguo,
            id=item_id,
            title="Mock 详情作品",
            cover="http://mock.local/cover.jpg",
            author="Mock作者",
            desc="Mock详情描述",
            segments=[
                SegmentInfo(id="seg_1", title="第 1 集", index=1, locked=False),
                SegmentInfo(id="seg_2", title="第 2 集", index=2, locked=False),
            ],
        )

    async def resolve_download(self, resource_id: str, **kwargs) -> list[dict]:
        return [{
            "download_mode": "direct",
            "resource_id": resource_id,
            "url": "https://mock.local/file.mp4",
            "suggested_filename": f"mock_{resource_id}.mp4",
        }]

@pytest.fixture
def fake_platform():
    return FakeMockPlatform()
