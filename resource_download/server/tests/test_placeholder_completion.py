"""占位功能收口后的真实实现契约测试。"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.jobs.manager import JobManager
from app.logger import metrics_tracker
from app.main import app
from app.models import PlatformName


def test_configured_client_release_manifest_reports_update():
    settings = get_settings()
    settings.client_latest_version = "1.2.0"
    settings.client_minimum_version = "1.1.0"
    settings.client_update_url = "https://download.example.com/rd-1.2.0.exe"
    settings.client_update_sha256 = "a" * 64
    settings.client_release_notes = "真实更新"
    settings.client_update_rollout_percentage = 100

    with TestClient(app) as client:
        response = client.get(
            "/v1/version?current_version=1.0.0&install_id=install-a"
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["update_check_enabled"] is True
    assert payload["has_update"] is True
    assert payload["mandatory"] is True
    assert payload["download_url"].startswith("https://")
    assert payload["sha256"] == "a" * 64


def test_fanqie_discover_maps_real_home_rows(monkeypatch):
    from platforms.fanqie import platform as platform_module

    monkeypatch.setattr(
        platform_module.web_ssr,
        "get_home_discover",
        lambda kind, limit: [
            {
                "book_id": "book-1",
                "title": f"{kind}-title",
                "cover": "https://p3-novel.byteimg.com/cover.jpg",
                "author": "作者",
                "desc": "简介",
                "category": "都市",
                "update_time": "1785304000",
                "latest_chapter": "第十章",
            }
        ][:limit],
    )
    items = asyncio.run(platform_module.FanqiePlatform().discover("new", limit=5))
    assert len(items) == 1
    assert items[0].platform == PlatformName.fanqie
    assert items[0].badge == "新"
    assert items[0].extra["update_time"] == "1785304000"


def test_job_speed_is_measured_from_growing_output(tmp_path, monkeypatch):
    from app.jobs import manager as manager_module

    settings = Settings(data_dir=tmp_path)
    manager = JobManager(settings)
    job_dir = settings.outputs_dir / "job-speed"
    job_dir.mkdir(parents=True)
    media = job_dir / "episode.enc.mp4"
    media.write_bytes(b"")
    samples = iter((100.0, 102.0))
    monkeypatch.setattr(manager_module.time, "monotonic", lambda: next(samples))

    assert manager._measure_speed("user:1", ["job-speed"]) == 0
    media.write_bytes(b"x" * (2 * 1024 * 1024))
    speed = manager._measure_speed("user:1", ["job-speed"])
    assert speed == 1024 * 1024
    assert manager._format_speed(speed) == "1.0 MB/s"


def test_http_requests_are_counted_automatically():
    before = metrics_tracker.get_summary()["total_requests"]
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert metrics_tracker.get_summary()["total_requests"] >= before + 1


def test_desktop_preferences_respect_remember_directory(tmp_path, monkeypatch):
    from client.desktop.main import WindowApi

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    api = WindowApi("https://api.example.com")
    api._download_dir = tmp_path / "chosen"
    api._persist_preferences(remember_directory=True)
    saved = json.loads(api._preferences_path.read_text(encoding="utf-8"))
    assert saved["download_directory"] == str(tmp_path / "chosen")

    api._persist_preferences(remember_directory=False)
    saved = json.loads(api._preferences_path.read_text(encoding="utf-8"))
    assert "download_directory" not in saved
    assert saved["install_id"]


def test_desktop_update_rejects_insecure_url_and_untrusted_installer(tmp_path, monkeypatch):
    from client.desktop.main import WindowApi

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    api = WindowApi("https://api.example.com")
    assert api.download_update("http://download.example.com/update.exe")["success"] is False

    untrusted = tmp_path / "outside.exe"
    untrusted.write_bytes(b"not-an-installer")
    result = api.install_update(str(untrusted))
    assert result["success"] is False
    assert result["message"] == "更新包路径无效"


def test_client_no_longer_contains_visible_placeholder_features():
    root = Path(__file__).resolve().parents[2]
    app_js = (root / "client" / "ui" / "app.js").read_text(encoding="utf-8")
    index_html = (root / "client" / "ui" / "index.html").read_text(encoding="utf-8")

    assert "内容服务后续接入" not in app_js
    assert "即将可用" not in app_js
    assert "即将上线" not in app_js
    assert 'btnLoadMore.addEventListener("click"' in app_js
    assert "download_update" in app_js
    assert "settingNameUseSuffix" not in index_html
