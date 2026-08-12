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
