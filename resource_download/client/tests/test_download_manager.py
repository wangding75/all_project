from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from client.desktop.download_manager import DownloadManager
from client.desktop.download_models import DownloadDescriptor
from client.desktop.download_repository import DownloadRepository


PAYLOAD = b"resource-download-client-test" * 1024


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        start = 0
        raw_range = self.headers.get("Range") or ""
        if raw_range.startswith("bytes="):
            start = int(raw_range.split("=", 1)[1].split("-", 1)[0])
        body = PAYLOAD[start:]
        self.send_response(206 if start else 200)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Range", f"bytes {start}-{len(PAYLOAD)-1}/{len(PAYLOAD)}")
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


def test_manager_persists_history_and_reopens(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    repo = DownloadRepository(tmp_path / "client.sqlite3")
    manager = DownloadManager(repo, tmp_path / "downloads", max_concurrent=2)
    task = manager.add_descriptor(
        DownloadDescriptor(
            platform="fixture",
            resource_id="resource-1",
            title="Fixture",
            suggested_filename="../safe?.bin",
            download_mode="direct",
            url=f"http://127.0.0.1:{server.server_port}/resource",
            range_supported=True,
        )
    )
    result = manager.wait_for(task.task_id, timeout=10)
    assert result is not None
    assert result.status == "success"
    assert open(result.local_path, "rb").read() == PAYLOAD
    manager.shutdown()
    server.shutdown()

    reopened = DownloadRepository(tmp_path / "client.sqlite3")
    assert [item.task_id for item in reopened.history()] == [task.task_id]
    reopened.close()


def test_manager_resume_from_part_file(tmp_path):
    repo = DownloadRepository(tmp_path / "client.sqlite3")
    manager = DownloadManager(repo, tmp_path / "downloads", autostart=False)
    descriptor = DownloadDescriptor(
        platform="fixture",
        resource_id="resource-2",
        suggested_filename="video.mp4",
        download_mode="direct",
        url="http://127.0.0.1:1/not-used",
        range_supported=True,
    )
    task = manager.add_descriptor(descriptor, enqueue=False)
    part = task.local_path + ".part"
    with open(part, "wb") as handle:
        handle.write(b"partial")
    assert part.endswith(".part")
    assert manager.repository.get(task.task_id).status == "pending"
    manager.shutdown(wait=False)


def test_manager_supports_proxy_descriptor_and_queue_controls(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    repo = DownloadRepository(tmp_path / "client.sqlite3")
    manager = DownloadManager(repo, tmp_path / "downloads", max_concurrent=1)
    first = manager.add_descriptor(
        DownloadDescriptor(
            platform="fixture",
            resource_id="proxy-1",
            suggested_filename="proxy.bin",
            download_mode="proxy",
            proxy_url=f"http://127.0.0.1:{server.server_port}/proxy",
        )
    )
    second = manager.add_descriptor(
        DownloadDescriptor(
            platform="fixture",
            resource_id="proxy-2",
            suggested_filename="proxy-2.bin",
            download_mode="proxy",
            proxy_url=f"http://127.0.0.1:{server.server_port}/proxy-2",
        ),
        enqueue=False,
    )
    paused = manager.pause_queue()
    assert paused["paused"] is True
    assert manager.queue_state()["paused"] is True
    manager.resume_queue()
    manager.enqueue(second.task_id)
    assert manager.wait_for(first.task_id, timeout=10).status == "success"
    assert manager.wait_for(second.task_id, timeout=10).status == "success"
    manager.shutdown()
    server.shutdown()


def test_manager_exposes_local_file_index_for_completed_download(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    repo = DownloadRepository(tmp_path / "client.sqlite3")
    manager = DownloadManager(repo, tmp_path / "downloads", max_concurrent=1)
    task = manager.add_descriptor(
        DownloadDescriptor(
            platform="fixture",
            resource_id="local-file-index",
            title="Local file index",
            suggested_filename="local.bin",
            download_mode="direct",
            url=f"http://127.0.0.1:{server.server_port}/local",
        )
    )
    result = manager.wait_for(task.task_id, timeout=10)
    assert result is not None and result.status == "success"
    files = manager.local_files()
    assert len(files) == 1
    assert files[0]["file_id"] == task.task_id
    assert files[0]["task_id"] == task.task_id
    assert files[0]["title"] == "Local file index"
    assert files[0]["name"] == "local.bin"
    assert files[0]["path"] == result.local_path
    assert files[0]["local_path"] == result.local_path
    assert files[0]["media_type"] == "application/octet-stream"
    assert files[0]["platform"] == "fixture"
    assert files[0]["size_bytes"] == len(PAYLOAD)
    assert files[0]["size_human"] == "29.0 KB"
    assert files[0]["exists"] is True
    assert files[0]["created_at"] == result.completed_at
    manager.shutdown()
    server.shutdown()
