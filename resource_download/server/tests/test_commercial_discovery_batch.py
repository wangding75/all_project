"""商业发现与批量任务 P0 服务端契约测试。"""

from __future__ import annotations

import asyncio
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

    async def discover(self, kind: str, *, limit: int = 24, **_kwargs):
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


def test_discover_forwards_real_filters_and_applies_episode_threshold(
    commercial_client,
    monkeypatch,
):
    calls = []

    class _FilteredPlatform:
        async def discover(self, kind, *, limit, **kwargs):
            calls.append((kind, limit, kwargs))
            return [
                DiscoverItem(
                    id="short",
                    title="玄幻短剧",
                    platform=PlatformName.hongguo,
                    extra={"episode_count": 8, "category": "玄幻"},
                ),
                DiscoverItem(
                    id="long",
                    title="玄幻长剧",
                    platform=PlatformName.hongguo,
                    extra={"episode_count": 30, "category": "玄幻"},
                ),
            ]

    monkeypatch.setattr(router_module, "get_platform", lambda _name: _FilteredPlatform())
    response = commercial_client.get(
        "/v1/discover?platform=hongguo&kinds=hot&genre=ai_series"
        "&sort=hot_collect&theme=玄幻&gender=男频&days=7"
        "&min_episode_count=20&keyword=玄幻",
        headers={"X-API-Key": "commercial-test-key"},
    )
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["sections"][0]["items"]] == ["long"]
    assert calls[0][2]["genre"] == "ai_series"
    assert calls[0][2]["sort"] == "hot_collect"
    assert calls[0][2]["theme"] == "玄幻"
    assert calls[0][2]["days"] == 7


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


def test_queue_bulk_control_returns_affected_and_skipped(
    commercial_client,
    monkeypatch,
):
    class _BulkManager:
        async def set_jobs_paused_for(self, _identity, job_ids, *, paused):
            assert paused is True
            assert job_ids == ["job-1", "missing"]
            return ["job-1"], ["missing"]

    monkeypatch.setattr(router_module, "get_job_manager", lambda: _BulkManager())
    response = commercial_client.post(
        "/v1/jobs/queue/bulk",
        headers={"X-API-Key": "commercial-test-key"},
        json={"job_ids": ["job-1", "missing", "job-1"], "action": "pause"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "action": "pause",
        "requested": 2,
        "affected": 1,
        "skipped": ["missing"],
    }


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


def test_cover_recognition_returns_real_similarity_candidate(tmp_path, monkeypatch):
    from PIL import Image

    from app import image_recognition

    source = BytesIO()
    Image.new("RGB", (240, 360), color=(180, 35, 70)).save(source, format="PNG")
    target = tmp_path / "target.jpg"
    Image.new("RGB", (240, 360), color=(180, 35, 70)).save(target, format="JPEG")

    class _CoverPlatform:
        async def discover(self, kind, *, limit):
            return [
                DiscoverItem(
                    id="poster-1",
                    title="相同海报",
                    cover="https://p3-reading-sign.fqnovelpic.com/poster.jpg",
                    platform=PlatformName.hongguo,
                    badge=kind,
                )
            ]

    monkeypatch.setattr(image_recognition, "get_platform", lambda _name: _CoverPlatform())
    monkeypatch.setattr(
        image_recognition,
        "register_cover_url",
        lambda _url: "/v1/covers/1234567890abcdef12345678.jpg",
    )
    monkeypatch.setattr(image_recognition, "materialize_cover", lambda _cover_id: target)

    result = asyncio.run(
        image_recognition.recognize_cover(
            source.getvalue(),
            platform_hint="hongguo",
            max_candidates=3,
        )
    )
    assert result.compared_count == 1
    assert result.candidates[0].content.id == "poster-1"
    assert result.candidates[0].confidence == "high"
    assert result.candidates[0].score > 0.95


def test_image_recognition_rejects_invalid_base64(commercial_client):
    response = commercial_client.post(
        "/v1/image/recognize",
        headers={"X-API-Key": "commercial-test-key"},
        json={"image_base64": "this-is-not-base64!", "platform_hint": "all"},
    )
    assert response.status_code == 400


def test_hongguo_people_index_uses_batched_real_metadata(monkeypatch):
    from platforms.hongguo import platform as platform_module

    class _HongguoApi:
        @staticmethod
        def browse(_genre, **_kwargs):
            return [
                {
                    "series_id": "series-1",
                    "title": "演员测试剧",
                    "cover": "https://p3-reading-sign.fqnovelpic.com/work.jpg",
                    "episode_cnt": 24,
                }
            ]

        @staticmethod
        def get_episodes_batch(series_ids, batch_size):
            assert series_ids == ["series-1"]
            assert batch_size == 20
            return {
                "series-1": {
                    "title": "演员测试剧",
                    "episode_cnt": 24,
                    "celebrities": [
                        {
                            "演员": "测试演员",
                            "角色": "主角",
                            "头像": "https://p3-reading-sign.fqnovelpic.com/avatar.jpg",
                            "简介": "演员资料",
                        }
                    ],
                }
            }, []

    monkeypatch.setattr(platform_module, "load_hongguo_api", lambda: _HongguoApi)
    monkeypatch.setattr(
        platform_module,
        "call_with_session_recovery",
        lambda operation: operation(),
    )
    result = asyncio.run(
        platform_module.HongguoPlatform().get_people_index(
            genre="short_play",
            work_limit=20,
        )
    )
    assert result.scanned_works == 1
    assert result.people[0].name == "测试演员"
    assert result.people[0].works[0].role == "主角"
    assert result.people[0].works[0].id == "series-1"


def test_hongguo_session_recovery_reconnects_and_retries_once(monkeypatch):
    from platforms.hongguo import bridge

    calls = {"operation": 0, "reset": 0, "ensure": 0}

    def _operation():
        calls["operation"] += 1
        if calls["operation"] == 1:
            raise RuntimeError("script has been destroyed")
        return "recovered"

    def _reset():
        calls["reset"] += 1

    def _ensure():
        calls["ensure"] += 1

    monkeypatch.setattr(bridge, "_reset_local_oracle", _reset)
    monkeypatch.setattr(bridge, "_ensure_hongguo_runtime", _ensure)

    assert bridge.call_with_session_recovery(_operation) == "recovered"
    assert calls == {"operation": 2, "reset": 1, "ensure": 2}


def test_hongguo_download_rejects_diagnostic_raw_output(tmp_path, monkeypatch):
    from platforms.hongguo import platform as platform_module

    class _Offline:
        OUT = ""
        STATE_DIR = ""

        @staticmethod
        def dl_series(*_args, **_kwargs):
            output = tmp_path / "episode.raw.mp4"
            output.write_bytes(b"diagnostic-bytevc")

    monkeypatch.setattr(platform_module, "load_hongguo_api", lambda: object())
    monkeypatch.setattr(platform_module, "load_offline_dl", lambda: _Offline)
    monkeypatch.setattr(
        platform_module,
        "call_with_session_recovery",
        lambda operation: operation(),
    )

    adapter = platform_module.HongguoPlatform()
    with pytest.raises(RuntimeError, match="proprietary ByteVC"):
        asyncio.run(
            adapter.download(
                "series-1",
                tmp_path,
                range_spec="1",
                options={"quality": "720p"},
            )
        )

    files = asyncio.run(
        adapter.download(
            "series-1",
            tmp_path,
            range_spec="1",
            options={"quality": "720p", "allow_raw": True},
        )
    )
    assert files == [tmp_path / "episode.raw.mp4"]
