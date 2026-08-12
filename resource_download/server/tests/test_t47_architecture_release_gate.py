"""T47 release-gate assertions for the frozen Server -> Client boundary."""

from __future__ import annotations

from pathlib import Path

from fastapi.routing import APIRoute

from app.main import app
from client.desktop.client_timer import ClientTimer
from client.desktop.download_manager import DownloadManager
from client.desktop.download_repository import DownloadRepository
from platforms.base import BasePlatform


ROOT = Path(__file__).resolve().parents[2]


def _routes() -> set[str]:
    return {route.path for route in app.routes if isinstance(route, APIRoute)}


def test_release_gate_has_only_resolve_and_proxy_download_server_contracts():
    routes = _routes()
    assert "/v1/resolve" in routes
    assert "/v1/downloads/proxy/{token}" in routes
    assert not any(path.startswith("/v1/jobs") for path in routes)
    assert not any(path.startswith("/v1/files") for path in routes)
    assert not any(path.startswith("/v1/automation") for path in routes)


def test_release_gate_server_owns_platform_resolution_but_not_download_storage():
    app_root = ROOT / "server" / "app"
    assert not list((app_root / "jobs").glob("*.py"))
    assert not list((app_root / "automation").glob("*.py"))
    assert not (app_root / "outputs").exists()

    config_source = (app_root / "config.py").read_text(encoding="utf-8")
    models_source = (app_root / "models.py").read_text(encoding="utf-8")
    assert "jobs_dir" not in config_source
    assert "outputs_dir" not in config_source
    assert "class JobFile" not in models_source
    assert "class JobResponse" not in models_source

    # Platform-private code exposes only resolution/streaming contracts to the
    # router.  A server-side file-producing download method is forbidden.
    assert not hasattr(BasePlatform, "download")
    assert hasattr(BasePlatform, "resolve_download")
    assert hasattr(BasePlatform, "stream_download")


def test_release_gate_client_owns_queue_progress_retry_sqlite_history_and_timer():
    manager_source = (ROOT / "client" / "desktop" / "download_manager.py").read_text(encoding="utf-8")
    repository_source = (ROOT / "client" / "desktop" / "download_repository.py").read_text(encoding="utf-8")
    timer_source = (ROOT / "client" / "desktop" / "client_timer.py").read_text(encoding="utf-8")
    for marker in ("pause_queue", "resume_queue", "retry", "wait_for", "history"):
        assert marker in manager_source
    for marker in ("CREATE TABLE IF NOT EXISTS download_tasks", "recover_interrupted", "def history"):
        assert marker in repository_source
    assert "class ClientTimer" in timer_source
    assert DownloadManager is not None
    assert DownloadRepository is not None
    assert ClientTimer is not None


def test_release_gate_client_code_has_no_server_job_file_automation_main_chain():
    client_root = ROOT / "client"
    for relative in ("ui/app.js", "desktop/main.py", "desktop/http_client.py"):
        source = (client_root / relative).read_text(encoding="utf-8")
        assert "/v1/jobs" not in source
        assert "/v1/files" not in source
        assert "/v1/automation" not in source
    assert "download_file" not in (client_root / "desktop/main.py").read_text(encoding="utf-8")


def test_release_gate_built_server_and_desktop_artifacts_exist():
    dist = ROOT / "dist"
    server_exe = dist / "RDServer.exe"
    client_exe = dist / "ResourceDownloader.exe"
    assert server_exe.is_file() and server_exe.stat().st_size > 1_000_000
    assert client_exe.is_file() and client_exe.stat().st_size > 1_000_000
