"""T46 structural acceptance: server no longer owns download jobs or files."""

from __future__ import annotations

from pathlib import Path

from fastapi.routing import APIRoute

from app.main import app


def _routes() -> set[str]:
    return {route.path for route in app.routes if isinstance(route, APIRoute)}


def test_server_job_file_and_automation_routes_are_absent():
    routes = _routes()
    assert "/v1/resolve" in routes
    assert "/v1/downloads/proxy/{token}" in routes
    assert not any(path.startswith("/v1/jobs") for path in routes)
    assert not any(path.startswith("/v1/files") for path in routes)
    assert not any(path.startswith("/v1/automation") for path in routes)


def test_resolve_and_proxy_keep_device_license_guard():
    guarded = {
        route.path
        for route in app.routes
        if any(
            getattr(dependency.call, "__name__", "") == "require_active_device_license"
            for dependency in getattr(getattr(route, "dependant", None), "dependencies", [])
        )
    }
    assert {"/v1/resolve", "/v1/downloads/proxy/{token}"} <= guarded


def test_server_has_no_job_file_automation_persistence_modules():
    app_root = Path(__file__).resolve().parents[1] / "app"
    assert not (app_root / "jobs" / "manager.py").exists()
    assert not (app_root / "automation" / "hongguo_monitor.py").exists()
    models_source = (app_root / "models.py").read_text(encoding="utf-8")
    assert "class JobFile" not in models_source
    assert "class JobResponse" not in models_source
    config_source = (app_root / "config.py").read_text(encoding="utf-8")
    assert "jobs_dir" not in config_source
    assert "outputs_dir" not in config_source


def test_desktop_main_chain_has_no_deprecated_server_file_dependency():
    client_root = Path(__file__).resolve().parents[2] / "client"
    for relative in ("ui/app.js", "desktop/main.py", "desktop/http_client.py"):
        source = (client_root / relative).read_text(encoding="utf-8")
        assert "/v1/jobs" not in source
        assert "/v1/files" not in source
        assert "/v1/automation" not in source
    assert "download_file" not in (client_root / "desktop/main.py").read_text(encoding="utf-8")
