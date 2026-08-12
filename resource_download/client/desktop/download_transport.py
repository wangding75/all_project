"""Direct/proxy HTTP transport for the local Download Manager."""

from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable


class DownloadCancelled(RuntimeError):
    pass


HeadersFactory = Callable[[str, str, dict[str, str]], dict[str, str]]


class HttpDownloadTransport:
    def __init__(self, *, timeout: float = 60.0, headers_factory: HeadersFactory | None = None) -> None:
        self.timeout = max(1.0, float(timeout))
        self.headers_factory = headers_factory

    def download(
        self,
        url: str,
        part_path: Path,
        *,
        headers: dict[str, str] | None = None,
        expected_size: int | None = None,
        range_supported: bool | None = None,
        progress: Callable[[int, int], None] | None = None,
        cancel_event=None,
        pause_event=None,
    ) -> tuple[int, int, bool]:
        """Download to ``.part`` and return (bytes, total, range_used)."""
        part_path.parent.mkdir(parents=True, exist_ok=True)
        current = part_path.stat().st_size if part_path.exists() else 0
        request_headers = {str(k): str(v) for k, v in dict(headers or {}).items()}
        range_used = bool(current and range_supported is not False)
        if range_used:
            request_headers["Range"] = f"bytes={current}-"
        if self.headers_factory:
            request_headers = self.headers_factory("GET", url, request_headers)
        request = urllib.request.Request(url, headers=request_headers, method="GET")
        try:
            response = urllib.request.urlopen(request, timeout=self.timeout)
        except urllib.error.HTTPError as exc:
            if exc.code == 416 and current and expected_size and current >= expected_size:
                return current, current, range_used
            raise
        status = int(getattr(response, "status", 200) or 200)
        append = range_used and status == 206
        if not append:
            current = 0
        raw_total = response.headers.get("Content-Range") or ""
        total = 0
        if "/" in raw_total:
            try:
                total = int(raw_total.rsplit("/", 1)[1])
            except ValueError:
                total = 0
        if not total:
            try:
                total = int(response.headers.get("Content-Length") or 0) + current
            except ValueError:
                total = 0
        total = max(total, int(expected_size or 0), current)
        mode = "ab" if append else "wb"
        try:
            with response, part_path.open(mode) as output:
                downloaded = current
                while True:
                    if cancel_event is not None and cancel_event.is_set():
                        raise DownloadCancelled("CLIENT_DOWNLOAD_CANCELLED")
                    while pause_event is not None and pause_event.is_set():
                        if cancel_event is not None and cancel_event.is_set():
                            raise DownloadCancelled("CLIENT_DOWNLOAD_CANCELLED")
                        pause_event.wait(0.1)
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    downloaded += len(chunk)
                    if progress:
                        progress(downloaded, total)
                output.flush()
            return downloaded, max(total, downloaded), append
        except Exception:
            raise
