"""Tests for the bounded, short-lived cover presentation cache."""

from __future__ import annotations

import os
import time
from types import SimpleNamespace

from app import media_cache


def test_cover_cache_prunes_expired_and_over_budget_files(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache" / "covers"
    cache_dir.mkdir(parents=True)
    settings = SimpleNamespace(
        data_dir=tmp_path,
        cover_cache_ttl_seconds=60,
        cover_cache_max_files=2,
        cover_cache_max_bytes=10,
        cover_cache_max_entries=2,
    )
    monkeypatch.setattr(media_cache, "get_settings", lambda: settings)

    expired = cache_dir / ("a" * 24 + ".jpg")
    oldest = cache_dir / ("b" * 24 + ".jpg")
    newest = cache_dir / ("c" * 24 + ".jpg")
    expired.write_bytes(b"expired")
    oldest.write_bytes(b"123456")
    newest.write_bytes(b"654321")
    old_time = time.time() - 120
    os.utime(expired, (old_time, old_time))
    os.utime(oldest, (old_time + 1, old_time + 1))
    os.utime(newest, (old_time + 2, old_time + 2))

    media_cache._prune_cache()

    assert not expired.exists()
    files = list(cache_dir.glob("*.jpg"))
    assert len(files) <= 2
    assert sum(path.stat().st_size for path in files) <= 10


def test_cover_url_index_is_bounded(tmp_path, monkeypatch):
    settings = SimpleNamespace(
        data_dir=tmp_path,
        cover_cache_ttl_seconds=60,
        cover_cache_max_files=2,
        cover_cache_max_bytes=10,
        cover_cache_max_entries=2,
    )
    monkeypatch.setattr(media_cache, "get_settings", lambda: settings)
    original = media_cache._cover_urls.copy()
    try:
        media_cache._cover_urls.clear()
        for index in range(3):
            assert media_cache.register_cover_url(
                f"https://p{index}.byteimg.com/cover.jpg"
            )
        assert len(media_cache._cover_urls) == 2
    finally:
        media_cache._cover_urls.clear()
        media_cache._cover_urls.update(original)


def test_materialize_cover_does_not_return_expired_target(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache" / "covers"
    cache_dir.mkdir(parents=True)
    settings = SimpleNamespace(
        data_dir=tmp_path,
        cover_cache_ttl_seconds=60,
        cover_cache_max_files=2,
        cover_cache_max_bytes=10,
        cover_cache_max_entries=2,
    )
    monkeypatch.setattr(media_cache, "get_settings", lambda: settings)
    target = cache_dir / ("d" * 24 + ".jpg")
    target.write_bytes(b"expired")
    expired_at = time.time() - 120
    os.utime(target, (expired_at, expired_at))

    assert media_cache.materialize_cover("d" * 24) is None
    assert not target.exists()


def test_expired_cover_url_registration_is_not_fetchable(tmp_path, monkeypatch):
    settings = SimpleNamespace(
        data_dir=tmp_path,
        cover_cache_ttl_seconds=60,
        cover_cache_max_files=2,
        cover_cache_max_bytes=10,
        cover_cache_max_entries=2,
    )
    monkeypatch.setattr(media_cache, "get_settings", lambda: settings)
    original = media_cache._cover_urls.copy()
    try:
        media_cache._cover_urls.clear()
        cover_url = media_cache.register_cover_url("https://p.byteimg.com/cover.jpg")
        cover_id = cover_url.rsplit("/", 1)[1][:-4]
        media_cache._cover_urls[cover_id] = (
            "https://p.byteimg.com/cover.jpg",
            time.time() - 120,
        )
        assert media_cache.materialize_cover(cover_id) is None
        assert cover_id not in media_cache._cover_urls
    finally:
        media_cache._cover_urls.clear()
        media_cache._cover_urls.update(original)
