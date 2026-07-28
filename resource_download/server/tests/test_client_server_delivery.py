"""桌面客户端与服务端文件交付闭环集成测试。"""

from __future__ import annotations

import io
import urllib.error
import urllib.parse
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.jobs import get_job_manager
from app.jobs.manager import JobRecord
from app.main import app
from app.models import JobFile, JobStatus, PlatformName
from client.desktop import main as desktop


class _ResponseAdapter:
    """把 TestClient 响应适配为 urllib urlopen 的最小上下文接口。"""

    def __init__(self, content: bytes) -> None:
        self._stream = io.BytesIO(content)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self._stream.close()

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)


def test_remote_http_is_rejected_but_loopback_http_is_allowed() -> None:
    assert desktop.is_secure_api_base("http://127.0.0.1:8000")
    assert desktop.is_secure_api_base("http://localhost:8000")
    assert desktop.is_secure_api_base("https://download.example.com")
    assert not desktop.is_secure_api_base("http://download.example.com")
    assert not desktop.is_secure_api_base("not-a-url")


def test_filename_is_sanitized() -> None:
    assert desktop._safe_filename("../../bad:name?.txt") == "bad_name_.txt"
    assert desktop._safe_filename("") == "download.bin"


def test_client_assets_use_local_delivery_bridge() -> None:
    root = Path(__file__).resolve().parents[2]
    app_js = (root / "client" / "ui" / "app.js").read_text(encoding="utf-8")
    index_html = (root / "client" / "ui" / "index.html").read_text(encoding="utf-8")
    build_script = (root / "scripts" / "build_exe.py").read_text(encoding="utf-8")

    assert "download_file(" in app_js
    assert "downloadFileInBrowser" in app_js
    assert "/open`" not in app_js
    assert "下载到本机" in app_js
    assert 'id="btnChooseOutputDir"' in index_html
    assert '"--exclude-module=app"' in build_script
    assert '"--exclude-module=platforms"' in build_script


def test_authenticated_server_file_reaches_client_disk(tmp_path, monkeypatch) -> None:
    """真实 FastAPI 文件端点 -> 桌面桥 -> 客户机目录，并验证错误 Key 被拒绝。"""
    settings = get_settings()
    manager = get_job_manager()
    original = {
        "auth_mode": settings.auth_mode,
        "api_key": settings.api_key,
        "outputs_dir": manager.settings.data_dir,
        "jobs": manager._jobs,
    }

    server_data = tmp_path / "server-data"
    outputs = server_data / "outputs"
    job_id = "delivery001"
    server_file = outputs / job_id / "episode01.txt"
    server_file.parent.mkdir(parents=True)
    expected = "客户端—服务端联调成功\n".encode("utf-8")
    server_file.write_bytes(expected)

    try:
        settings.auth_mode = "dev"
        settings.api_key = "integration-ops-key"
        manager.settings.data_dir = server_data
        manager._jobs = {
            job_id: JobRecord(
                job_id=job_id,
                platform=PlatformName.fanqie,
                item_id="book-001",
                range_spec="1",
                options={},
                status=JobStatus.success,
                files=[
                    JobFile(
                        file_id=f"{job_id}/{server_file.name}",
                        name=server_file.name,
                        size=len(expected),
                        path=str(server_file),
                    )
                ],
                owner_kind="api_key",
            )
        }

        client = TestClient(app)

        def fake_urlopen(request, timeout=0):  # noqa: ARG001
            parsed = urllib.parse.urlparse(request.full_url)
            response = client.get(parsed.path, headers=dict(request.header_items()))
            if response.status_code >= 400:
                raise urllib.error.HTTPError(
                    request.full_url,
                    response.status_code,
                    "download rejected",
                    response.headers,
                    io.BytesIO(response.content),
                )
            return _ResponseAdapter(response.content)

        monkeypatch.setattr(desktop.urllib.request, "urlopen", fake_urlopen)

        bridge = desktop.WindowApi("https://download.example.com")
        bridge._download_dir = tmp_path / "client-downloads"
        file_id = f"{job_id}/{server_file.name}"

        rejected = bridge.download_file(file_id, server_file.name, api_key="wrong-key")
        assert rejected["success"] is False
        assert not list(bridge._download_dir.rglob("*.txt"))

        result = bridge.download_file(
            file_id,
            server_file.name,
            api_key="integration-ops-key",
        )
        assert result["success"] is True
        local_path = Path(str(result["path"]))
        assert local_path == bridge._download_dir / job_id / server_file.name
        assert local_path.read_bytes() == expected
        assert not list(bridge._download_dir.rglob("*.part"))
    finally:
        settings.auth_mode = original["auth_mode"]
        settings.api_key = original["api_key"]
        manager.settings.data_dir = original["outputs_dir"]
        manager._jobs = original["jobs"]
