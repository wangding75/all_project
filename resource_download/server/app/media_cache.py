"""受控封面代理：缓存上游图片并统一转换为浏览器可显示的 JPEG。"""

from __future__ import annotations

import hashlib
import os
import threading
import uuid
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests

from app.config import get_settings

_MAX_SOURCE_BYTES = 8 * 1024 * 1024
_ALLOWED_HOST_SUFFIXES = (
    ".fqnovelpic.com",
    ".byteimg.com",
    ".bytedance.com",
)
_cover_urls: dict[str, str] = {}
_cover_lock = threading.Lock()


def _safe_source_url(url: str) -> tuple[str, str] | None:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return None
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not any(
        hostname.endswith(suffix) for suffix in _ALLOWED_HOST_SUFFIXES
    ):
        return None
    stable_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    return stable_url, url


def register_cover_url(url: str | None) -> str | None:
    """登记可信上游封面，返回同源、不可伪造 SSRF 目标的缓存 URL。"""
    if not url:
        return None
    safe = _safe_source_url(str(url))
    if safe is None:
        return None
    stable_url, request_url = safe
    cover_id = hashlib.sha256(stable_url.encode("utf-8")).hexdigest()[:24]
    with _cover_lock:
        _cover_urls[cover_id] = request_url
    return f"/v1/covers/{cover_id}.jpg"


def _cover_path(cover_id: str) -> Path:
    cache_dir = get_settings().data_dir / "cache" / "covers"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{cover_id}.jpg"


def materialize_cover(cover_id: str) -> Path | None:
    """下载已登记封面并转成 JPEG；未知 ID 不发起任何网络请求。"""
    if len(cover_id) != 24 or any(ch not in "0123456789abcdef" for ch in cover_id):
        return None
    target = _cover_path(cover_id)
    if target.is_file() and target.stat().st_size > 0:
        return target

    with _cover_lock:
        source_url = _cover_urls.get(cover_id)
    if not source_url:
        return None

    response = requests.get(
        source_url,
        headers={
            "User-Agent": "Mozilla/5.0 ResourceDownloader/1.0",
            "Referer": "https://novel.snssdk.com/",
        },
        timeout=(5, 20),
    )
    response.raise_for_status()
    data = response.content
    if not data or len(data) > _MAX_SOURCE_BYTES:
        raise ValueError("cover payload is empty or exceeds 8 MB")

    from PIL import Image
    from pillow_heif import register_heif_opener

    register_heif_opener()
    with Image.open(BytesIO(data)) as image:
        image.thumbnail((720, 1080))
        rgb = image.convert("RGB")
        temp = target.with_name(f"{target.name}.{uuid.uuid4().hex}.tmp")
        try:
            rgb.save(temp, format="JPEG", quality=88, optimize=True)
            os.replace(temp, target)
        finally:
            temp.unlink(missing_ok=True)
    return target
