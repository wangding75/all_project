"""商业发现与批量任务 P0 服务端契约测试。"""

from __future__ import annotations

from types import SimpleNamespace
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import get_db
from app.main import app
from app.models import DiscoverItem, JobStatus, PlatformName
from app.api import router as router_module


class _DiscoverPlatform:
    def __init__(self, platform: PlatformName, fail: bool = False):
        self.platform = platform
        self.fail = fail

    async def discover(self, kind: str, *, limit: int = 24):
        if self.fail:
            raise RuntimeError(f"{self.platform.value} unavailable")
        return [
            DiscoverItem(
                rank=1 if kind == "hot" else None,
                id=f"{self.platform.value}-{kind}-1",
                title=f"{self.platform.value} {kind}",
                platform=self.platform,
                source_label=self.platform.value,
                badge="热" if kind == "hot" else "新",
            )
        ][:limit]


class _BatchManager:
    def __init__(self):
        self.created = []

    async def list_jobs_for(self, *_args, **_kwargs):
        return [], 0

    async def create_job(self, **kwargs):
        self.created.append(kwargs)
        return SimpleNamespace(
            job_id=f"job-{len(self.created)}",
            platform=kwargs["platform"],
            item_id=kwargs["item_id"],
            status=JobStatus.pending,
        )


@pytest.fixture
def commercial_client():
    settings = get_settings()
    settings.auth_mode = "dev"
    settings.api_key = "commercial-test-key"

    def _db_override():
        yield object()

    app.dependency_overrides[get_db] = _db_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_discover_returns_live_data_and_degrades_per_platform(
    commercial_client,
    monkeypatch,
):
    def _platform(name):
        platform = name if isinstance(name, PlatformName) else PlatformName(name)
        return _DiscoverPlatform(platform, fail=platform == PlatformName.fanqie)

    monkeypatch.setattr(router_module, "get_platform", _platform)
    response = commercial_client.get(
        "/v1/discover?platform=all&kinds=hot,new&limit=12",
        headers={"X-API-Key": "commercial-test-key"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "live"
    assert [section["kind"] for section in payload["sections"]] == ["hot", "new"]
    assert payload["sections"][0]["items"][0]["id"] == "hongguo-hot-1"
    assert "fanqie" in payload["sections"][0]["platform_errors"]


def test_discover_rejects_unknown_kind(commercial_client):
    response = commercial_client.get(
        "/v1/discover?platform=hongguo&kinds=unknown",
        headers={"X-API-Key": "commercial-test-key"},
    )
    assert response.status_code == 400


def test_batch_jobs_create_each_item_and_return_batch_result(
    commercial_client,
    monkeypatch,
):
    manager = _BatchManager()
    monkeypatch.setattr(router_module, "get_job_manager", lambda: manager)
    monkeypatch.setattr(
        router_module,
        "get_platform",
        lambda name: SimpleNamespace(name=str(name)),
    )

    response = commercial_client.post(
        "/v1/jobs/batch",
        headers={"X-API-Key": "commercial-test-key"},
        json={
            "items": [
                {"platform": "hongguo", "id": "hg-1", "range": "all"},
                {"platform": "fanqie", "id": "fq-1", "range": "1-10"},
            ],
            "queue_mode": "enqueue",
            "duplicate_policy": "skip_completed",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["batch_id"].startswith("batch-")
    assert [item["job_id"] for item in payload["created"]] == ["job-1", "job-2"]
    assert payload["skipped"] == []
    assert payload["errors"] == []
    assert manager.created[1]["range_spec"] == "1-10"


def test_batch_jobs_validate_non_empty_items(commercial_client):
    response = commercial_client.post(
        "/v1/jobs/batch",
        headers={"X-API-Key": "commercial-test-key"},
        json={"items": []},
    )
    assert response.status_code == 422


def test_batch_resolve_returns_success_and_per_item_error(
    commercial_client,
    monkeypatch,
):
    async def _search_one(platform, query, _page):
        if query == "found-id" and platform == PlatformName.hongguo:
            from app.models import SearchItem

            return [
                SearchItem(
                    id="resolved-1",
                    title="识别成功",
                    platform=PlatformName.hongguo,
                    source_label="红果短剧",
                )
            ], None
        return [], f"{platform.value} not found"

    monkeypatch.setattr(router_module, "_search_one", _search_one)
    response = commercial_client.post(
        "/v1/batch/resolve",
        headers={"X-API-Key": "commercial-test-key"},
        json={
            "inputs": ["found-id", "missing-id"],
            "platform_hint": "all",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["input"] == "found-id"
    assert payload["items"][0]["content"]["id"] == "resolved-1"
    assert payload["errors"][0]["input"] == "missing-id"
    assert payload["errors"][0]["code"] == "NOT_FOUND"


def test_cover_cache_rejects_arbitrary_hosts_and_converts_to_jpeg(
    tmp_path,
    monkeypatch,
):
    from PIL import Image

    from app import media_cache

    settings = get_settings()
    settings.data_dir = tmp_path
    media_cache._cover_urls.clear()

    assert media_cache.register_cover_url("https://example.com/private") is None
    proxy_url = media_cache.register_cover_url(
        "https://p3-reading-sign.fqnovelpic.com/novel-pic/test.heic?signature=one"
    )
    assert proxy_url and proxy_url.startswith("/v1/covers/")
    cover_id = proxy_url.rsplit("/", 1)[1].removesuffix(".jpg")

    source = BytesIO()
    Image.new("RGB", (20, 30), color=(220, 20, 60)).save(source, format="PNG")

    class _Response:
        content = source.getvalue()

        @staticmethod
        def raise_for_status():
            return None

    monkeypatch.setattr(media_cache.requests, "get", lambda *_args, **_kwargs: _Response())
    path = media_cache.materialize_cover(cover_id)
    assert path is not None and path.is_file()
    assert path.read_bytes()[:2] == b"\xff\xd8"
    assert media_cache.materialize_cover("not-a-valid-cover-id") is None


def test_hongguo_session_recovery_reconnects_and_retries_once(monkeypatch):
    from platforms import runtime
    from platforms.hongguo import bridge

    calls = {"operation": 0, "reset": 0, "probe": 0}

    def _operation():
        calls["operation"] += 1
        if calls["operation"] == 1:
            raise RuntimeError("script has been destroyed")
        return "recovered"

    def _reset():
        calls["reset"] += 1

    def _probe(**kwargs):
        calls["probe"] += 1
        assert kwargs == {"try_start_agent": True, "try_start_apps": True}

    monkeypatch.setattr(bridge, "_reset_local_oracle", _reset)
    monkeypatch.setattr(runtime, "probe_all_runtimes", _probe)

    assert bridge.call_with_session_recovery(_operation) == "recovered"
    assert calls == {"operation": 2, "reset": 1, "probe": 1}
