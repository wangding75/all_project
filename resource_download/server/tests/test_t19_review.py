"""Deterministic regression coverage for the T19 review findings."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.config import Settings, get_settings
from app.errors import sanitize_error_text
from app.jobs.manager import JobManager, JobRecord
from app.models import JobStatus, PlatformName
from app.options import split_job_options, validate_range_spec
from app.security_boot import assert_production_secrets
from app.api.router import health
from platforms.fanqie.client import api_once
from platforms.fanqie.platform import FanqiePlatform
from platforms.hongguo.platform import HongguoPlatform


def test_fanqie_web_download_returns_durable_artifact(tmp_path, monkeypatch):
    async def run():
        monkeypatch.setattr(
            "platforms.fanqie.web_ssr.get_book_page",
            lambda *_args, **_kwargs: (
                "A/Book",
                [{"item_id": "1", "title": "One", "is_locked": False}],
                {},
                {},
            ),
        )
        monkeypatch.setattr(
            "platforms.fanqie.web_ssr.download_chapter",
            lambda *_args, **_kwargs: ("One", "non-empty chapter"),
        )
        paths = await FanqiePlatform().download("123", tmp_path, range_spec="1")
        assert len(paths) == 1
        assert paths[0].is_file()
        assert paths[0].stat().st_size > 0
        assert paths[0].resolve().is_relative_to(tmp_path.resolve())

    asyncio.run(run())


def test_hongguo_vendor_globals_are_isolated(tmp_path, monkeypatch):
    class FakeOffline:
        OUT = ""
        STATE_DIR = ""

        def dl_series(self, item_id, **_kwargs):
            out = Path(self.OUT)
            state = Path(self.STATE_DIR)
            state.mkdir(parents=True, exist_ok=True)
            time.sleep(0.02)
            (out / f"{item_id}.mp4").write_bytes(item_id.encode())

    fake = FakeOffline()
    monkeypatch.setattr("platforms.hongguo.platform.load_hongguo_api", lambda: object())
    monkeypatch.setattr("platforms.hongguo.platform.load_offline_dl", lambda: fake)
    monkeypatch.setattr("platforms.hongguo.platform.call_with_session_recovery", lambda op: op())

    async def run():
        first, second = await asyncio.gather(
            HongguoPlatform().download("A", tmp_path / "A", options={"quality": "1080p"}),
            HongguoPlatform().download("B", tmp_path / "B", options={"quality": "1080p"}),
        )
        assert [p.name for p in first] == ["A.mp4"]
        assert [p.name for p in second] == ["B.mp4"]
        assert not list((tmp_path / "A").glob("B*"))
        assert not list((tmp_path / "B").glob("A*"))

    asyncio.run(run())


def test_fanqie_tls_verification_defaults_true(monkeypatch):
    seen = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    monkeypatch.setattr("platforms.fanqie.client.sign", lambda *_args: {})
    monkeypatch.setattr(
        "platforms.fanqie.client.requests.request",
        lambda *args, **kwargs: (seen.update(kwargs) or Response()),
    )
    settings = get_settings()
    original = settings.fanqie_ca_bundle
    settings.fanqie_ca_bundle = ""
    try:
        assert api_once("GET", "/test", signed=False) == {"ok": True}
        assert seen["verify"] is True
    finally:
        settings.fanqie_ca_bundle = original


def test_jobfile_boundary_and_secret_persistence(tmp_path):
    settings = Settings(data_dir=tmp_path)
    manager = JobManager(settings)
    outside = tmp_path.parent / "outside-secret.txt"
    outside.write_text("secret", encoding="utf-8")
    record = JobRecord(
        job_id="safe1",
        platform=PlatformName.fanqie,
        item_id="1",
        range_spec="all",
        options={"title": "safe"},
        runtime_options={"cookie": "cookie-secret"},
        status=JobStatus.success,
    )
    from app.models import JobFile

    record.files = [JobFile(file_id="safe1/outside", name="outside", path=str(outside))]
    manager._jobs[record.job_id] = record
    manager._persist(record)
    payload = json.loads((settings.jobs_dir / "safe1.json").read_text(encoding="utf-8"))
    assert "cookie-secret" not in json.dumps(payload)
    assert str(outside) not in json.dumps(payload)
    assert manager.resolve_file("safe1/outside") is None


def test_options_and_error_bounds():
    with pytest.raises(ValueError):
        validate_range_spec("1-1000000000")
    with pytest.raises(ValueError):
        split_job_options(PlatformName.hongguo, {"concurrency": 1_000_000})
    safe = sanitize_error_text(
        "Authorization: Bearer super-secret https://host/path?token=abc C:\\private\\x.txt"
    )
    assert "super-secret" not in safe
    assert "token=abc" not in safe
    assert "C:\\private" not in safe


def test_invalid_auth_mode_fails_closed():
    settings = Settings(auth_mode="dev", host="127.0.0.1")
    settings.auth_mode = "invalid"  # type: ignore[assignment]
    with pytest.raises(RuntimeError, match="AUTH_MODE"):
        assert_production_secrets(settings)


def test_public_health_does_not_expose_installation_paths():
    payload = asyncio.run(health()).model_dump_json()
    assert "vendor_path" not in payload
    assert "config_path" not in payload
    assert "agent_bin" not in payload
    assert "D:\\\\github" not in payload


def test_terminal_retention_includes_jobs_with_files(tmp_path):
    settings = Settings(data_dir=tmp_path, max_history_jobs=3)
    manager = JobManager(settings)
    for index in range(5):
        record = JobRecord(
            job_id=f"old{index}",
            platform=PlatformName.hongguo,
            item_id=str(index),
            range_spec="all",
            options={},
            status=JobStatus.success,
            updated_at=f"2026-01-01T00:0{index}:00+00:00",
        )
        output = settings.outputs_dir / record.job_id
        output.mkdir(parents=True, exist_ok=True)
        (output / "x.mp4").write_bytes(b"x")
        from app.models import JobFile

        record.files = [JobFile(file_id=f"{record.job_id}/x.mp4", name="x.mp4", path=str(output / "x.mp4"))]
        manager._jobs[record.job_id] = record
        manager._persist(record)
    manager._evict_old_completed_jobs()
    assert len(manager._jobs) == 3
    assert not (settings.jobs_dir / "old0.json").exists()
