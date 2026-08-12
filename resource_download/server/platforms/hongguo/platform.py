"""红果平台适配器：复用 vendor/hongguo 的 API + 下载解密。"""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import Any

from app.models import (
    DetailResponse,
    DiscoverItem,
    PeopleResponse,
    PersonProfile,
    PersonWork,
    PlatformName,
    SearchItem,
    SegmentInfo,
)
from platforms.base import BasePlatform, ProgressCallback
from platforms.hongguo.bridge import (
    HongguoVendorError,
    call_with_session_recovery,
    load_hongguo_api,
    load_offline_dl,
    vendor_ready,
)


# ``offline_dl`` is a legacy vendor module whose output and state locations
# are module globals.  Until the vendor exposes an instance API, serialize the
# complete call so concurrent RD jobs cannot overwrite one another's paths.
_OFFLINE_DL_LOCK = threading.RLock()


class HongguoPlatform(BasePlatform):
    name = PlatformName.hongguo.value

    async def discover(
        self,
        kind: str,
        *,
        limit: int = 24,
        **kwargs: Any,
    ) -> list[DiscoverItem]:
        """红果真实热榜/今日上新。

        热榜使用短剧分类按热度排序；上新使用红果官方“今日上新”标记。
        列表接口免签，仍复用 vendor 配置、缓存和响应解析。
        """

        def _run() -> list[DiscoverItem]:
            from platforms.hongguo.bridge import ensure_config

            ensure_config()
            H = load_hongguo_api()
            bounded_limit = max(1, min(int(limit), 50))
            genre = str(kwargs.get("genre") or "short_play")
            if kind == "hot":
                rows = H.browse(
                    genre,
                    theme=kwargs.get("theme"),
                    setting=kwargs.get("setting"),
                    background=kwargs.get("background"),
                    sort=str(kwargs.get("sort") or "hot_score"),
                    gender=kwargs.get("gender"),
                    days=kwargs.get("days"),
                    status=kwargs.get("status"),
                    max_items=bounded_limit,
                ) or []
            elif kind == "new":
                rows = H.latest(
                    genre,
                    only_today=bool(kwargs.get("only_today", True)),
                    max_items=bounded_limit,
                ) or []
            else:
                raise ValueError(f"unsupported discover kind: {kind}")

            items: list[DiscoverItem] = []
            for index, row in enumerate(rows[:bounded_limit], start=1):
                sid = str(row.get("series_id") or row.get("id") or "")
                if not sid:
                    continue
                items.append(
                    DiscoverItem(
                        rank=index if kind == "hot" else None,
                        id=sid,
                        title=str(row.get("title") or sid),
                        cover=str(row.get("cover") or "") or None,
                        author=str(row.get("copyright") or "") or None,
                        desc=str(row.get("intro") or "") or None,
                        platform=PlatformName.hongguo,
                        source_label="红果短剧",
                        badge="热" if kind == "hot" else "新",
                        extra={
                            "episode_count": row.get("episode_cnt"),
                            "score": row.get("score"),
                            "play_count": row.get("play_cnt"),
                            "category": row.get("category"),
                            "today": row.get("today"),
                            "genre": genre,
                            "premiere": row.get("premiere"),
                            "comment_count": row.get("comment_count"),
                            "duration": row.get("duration"),
                        },
                    )
                )
            return items

        try:
            return await asyncio.to_thread(_run)
        except HongguoVendorError:
            raise
        except Exception as exc:  # noqa: BLE001
            from app.errors import format_platform_error

            raise RuntimeError(format_platform_error(exc)) from exc

    async def search(self, query: str, page: int = 1, **kwargs: Any) -> list[SearchItem]:
        def _run() -> list[SearchItem]:
            from platforms.hongguo.bridge import ensure_config

            ensure_config()  # 缺配置时抛清晰中文错误，避免 FileNotFound 难懂
            H = load_hongguo_api()
            # 上游 search(query, max_items=None) — page 暂不映射
            raw = H.search(query) or []
            items: list[SearchItem] = []
            start = max(0, (int(page) - 1) * 20)
            for row in raw[start : start + 20]:
                # 兼容 dict 或对象
                if isinstance(row, dict):
                    sid = str(row.get("series_id") or row.get("id") or row.get("book_id") or "")
                    title = str(row.get("title") or row.get("name") or sid)
                    cover = row.get("cover") or row.get("thumb_url")
                    desc = row.get("desc") or row.get("abstract")
                    extra = {k: v for k, v in row.items() if k not in {"title", "name", "cover"}}
                else:
                    sid = str(getattr(row, "series_id", None) or getattr(row, "id", "") or "")
                    title = str(getattr(row, "title", sid))
                    cover = getattr(row, "cover", None)
                    desc = getattr(row, "desc", None)
                    extra = {}
                if not sid:
                    continue
                items.append(
                    SearchItem(
                        id=sid,
                        title=title,
                        cover=str(cover) if cover else None,
                        desc=str(desc) if desc else None,
                        platform=PlatformName.hongguo,
                        source_label="红果短剧",
                        extra=extra,
                    )
                )
            return items

        try:
            return await asyncio.to_thread(call_with_session_recovery, _run)
        except HongguoVendorError:
            raise
        except Exception as exc:  # noqa: BLE001
            from app.errors import format_platform_error

            raise RuntimeError(format_platform_error(exc)) from exc

    async def get_detail(self, item_id: str, **kwargs: Any) -> DetailResponse:
        def _run() -> DetailResponse:
            H = load_hongguo_api()
            meta, eps = H.get_episodes(str(item_id))
            meta = meta or {}
            title = str(meta.get("title") or item_id)
            segments: list[SegmentInfo] = []
            for i, ep in enumerate(eps or [], start=1):
                if isinstance(ep, dict):
                    vid = str(ep.get("vid") or ep.get("video_id") or ep.get("id") or "")
                    idx = int(ep.get("index") or i)
                    etitle = str(ep.get("title") or f"第{idx}集")
                else:
                    vid = str(getattr(ep, "vid", "") or "")
                    idx = int(getattr(ep, "index", i) or i)
                    etitle = str(getattr(ep, "title", f"第{idx}集"))
                if not vid:
                    continue
                segments.append(SegmentInfo(id=vid, title=etitle, index=idx, locked=False))
            return DetailResponse(
                platform=PlatformName.hongguo,
                id=str(item_id),
                title=title,
                cover=str(meta.get("cover") or "") or None,
                author=None,
                desc=str(meta.get("status") or meta.get("desc") or "") or None,
                segments=segments,
                extra={
                    "episode_cnt": meta.get("episode_cnt"),
                    "status": meta.get("status"),
                    "play_count": meta.get("play_cnt"),
                    "followed_count": meta.get("followed_cnt"),
                    "create_time": meta.get("create_time"),
                    "category": meta.get("category") or [],
                    "celebrities": meta.get("celebrities") or [],
                    "vendor": vendor_ready(),
                },
            )

        try:
            return await asyncio.to_thread(call_with_session_recovery, _run)
        except HongguoVendorError:
            raise
        except Exception as exc:  # noqa: BLE001
            from app.errors import format_platform_error

            raise RuntimeError(format_platform_error(exc)) from exc

    async def resolve_download(
        self,
        resource_id: str,
        *,
        title: str = "",
        range_spec: str = "all",
        options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Resolve Hongguo episodes to short-lived CDN descriptors.

        All Hongguo API/signing/runtime work remains in this server adapter;
        the Desktop Client only receives a temporary URL and safe metadata.
        The legacy file-producing ``download`` method is intentionally not
        called by this path.
        """
        from app.options import validate_range_spec

        range_spec = validate_range_spec(range_spec)
        options = dict(options or {})

        def _run() -> list[dict[str, Any]]:
            H = load_hongguo_api()
            meta, episodes = H.get_episodes(str(resource_id))
            meta = meta or {}
            rows = list(episodes or [])
            selected: set[int] | None = None
            if range_spec not in {"", "all", "*"}:
                selected = set()
                for part in range_spec.split(","):
                    if "-" in part:
                        start, end = (int(value) for value in part.split("-", 1))
                        selected.update(range(min(start, end), max(start, end) + 1))
                    else:
                        selected.add(int(part))
            chosen: list[dict[str, Any]] = []
            for position, episode in enumerate(rows, start=1):
                if not isinstance(episode, dict):
                    continue
                index = int(episode.get("index") or position)
                if selected is not None and index not in selected:
                    continue
                vid = str(episode.get("vid") or episode.get("video_id") or episode.get("id") or "")
                if vid:
                    chosen.append({"index": index, "vid": vid, "title": str(episode.get("title") or f"第{index}集")})
            if not chosen and str(resource_id).strip():
                chosen = [{"index": 1, "vid": str(resource_id), "title": title or "资源"}]
            urls = H.get_video_urls([item["vid"] for item in chosen])
            result: list[dict[str, Any]] = []
            for item in chosen:
                info = dict(urls.get(item["vid"]) or {})
                url = str(info.get("url") or "")
                if not url:
                    continue
                safe_title = title or str(meta.get("title") or resource_id)
                result.append(
                    {
                        "platform": self.name,
                        "resource_id": item["vid"],
                        "title": safe_title,
                        "media_type": "video/mp4",
                        "suggested_filename": f"{safe_title}_第{item['index']:03d}集.mp4",
                        "download_mode": "direct",
                        "url": url,
                        "headers": {"User-Agent": "ResourceDownloader/Client"},
                        "size_bytes": info.get("size") or None,
                        "range_supported": True,
                        "extra": {"episode_index": item["index"], "definition": info.get("definition")},
                    }
                )
            return result

        try:
            return await asyncio.to_thread(call_with_session_recovery, _run)
        except HongguoVendorError:
            raise
        except Exception as exc:  # noqa: BLE001
            from app.errors import format_platform_error

            raise RuntimeError(format_platform_error(exc)) from exc

    async def get_people_index(
        self,
        *,
        genre: str = "short_play",
        work_limit: int = 20,
    ) -> PeopleResponse:
        """Build a real actor/works index from hot works plus batched series metadata."""

        def _run() -> PeopleResponse:
            H = load_hongguo_api()
            bounded_limit = max(1, min(int(work_limit), 30))
            rows = H.browse(
                genre,
                sort="hot_score",
                max_items=bounded_limit,
            ) or []
            by_id = {
                str(row.get("series_id") or row.get("id") or ""): row
                for row in rows
                if row.get("series_id") or row.get("id")
            }
            metadata, failures = H.get_episodes_batch(list(by_id), batch_size=20)
            people: dict[str, PersonProfile] = {}
            for series_id, meta in metadata.items():
                row = by_id.get(str(series_id), {})
                for celebrity in meta.get("celebrities") or []:
                    name = str(celebrity.get("演员") or "").strip()
                    if not name:
                        continue
                    profile = people.setdefault(
                        name,
                        PersonProfile(
                            name=name,
                            avatar=str(celebrity.get("头像") or "") or None,
                            intro=str(celebrity.get("简介") or ""),
                        ),
                    )
                    if any(work.id == str(series_id) for work in profile.works):
                        continue
                    profile.works.append(
                        PersonWork(
                            id=str(series_id),
                            title=str(row.get("title") or meta.get("title") or series_id),
                            cover=str(row.get("cover") or meta.get("cover") or "") or None,
                            role=str(celebrity.get("角色") or ""),
                            episode_count=int(
                                row.get("episode_cnt") or meta.get("episode_cnt") or 0
                            ),
                        )
                    )
            ordered = sorted(
                people.values(),
                key=lambda profile: (-len(profile.works), profile.name),
            )
            return PeopleResponse(
                people=ordered,
                scanned_works=len(by_id),
                errors=[str(item.get("error") or "") for item in failures[:10]],
            )

        try:
            return await asyncio.to_thread(call_with_session_recovery, _run)
        except HongguoVendorError:
            raise
        except Exception as exc:  # noqa: BLE001
            from app.errors import format_platform_error

            raise RuntimeError(format_platform_error(exc)) from exc

    async def download(
        self,
        item_id: str,
        output_dir: Path,
        *,
        range_spec: str = "all",
        options: dict[str, Any] | None = None,
        progress: ProgressCallback | None = None,
    ) -> list[Path]:
        from app.options import split_job_options, validate_range_spec

        persisted_options, runtime_options = split_job_options(PlatformName.hongguo, options)
        options = {**persisted_options, **runtime_options}
        range_spec = validate_range_spec(range_spec)
        quality = str(options.get("quality") or "best")
        concurrency = int(options.get("concurrency") or options.get("c") or 2)
        download_cover = bool(options.get("download_cover"))
        download_desc = bool(options.get("download_desc"))
        allow_raw = bool(options.get("allow_raw"))
        naming = options.get("naming") if isinstance(options.get("naming"), dict) else {}

        def _run() -> list[Path]:
            import re

            from platforms.naming import format_segment_filename

            H = load_hongguo_api()
            ODL = load_offline_dl()
            output_dir.mkdir(parents=True, exist_ok=True)

            # 让上游下载落到我们的 job 目录.  This assignment and the
            # vendor call must remain in one critical section (see above).
            if progress:
                progress(1.0, "prepare series")

            # 可选：简介元数据
            episode_titles: dict[int, str] = {}
            if download_desc or download_cover or naming:
                try:
                    meta, eps = H.get_episodes(str(item_id))
                    meta = meta or {}
                    for position, episode in enumerate(eps or [], start=1):
                        if isinstance(episode, dict):
                            index = int(episode.get("index") or position)
                            episode_titles[index] = str(
                                episode.get("title") or f"第{index}集"
                            )
                    if download_desc:
                        (output_dir / "简介.txt").write_text(
                            f"标题：{meta.get('title') or item_id}\n"
                            f"状态：{meta.get('status') or ''}\n"
                            f"集数：{meta.get('episode_cnt') or ''}\n\n"
                            f"{meta.get('desc') or meta.get('intro') or '暂无简介'}\n",
                            encoding="utf-8",
                        )
                    if download_cover and meta.get("cover"):
                        try:
                            import urllib.request

                            cover_url = str(meta["cover"])
                            urllib.request.urlretrieve(cover_url, str(output_dir / "封面.jpg"))
                        except Exception:
                            (output_dir / "封面.url.txt").write_text(
                                str(meta.get("cover") or ""), encoding="utf-8"
                            )
                except Exception:
                    pass

            # 复用上游整剧逻辑（内部签名+下载+解密）
            # This critical section protects the vendor module globals while
            # ``dl_series`` runs.
            with _OFFLINE_DL_LOCK:
                call_old_out = getattr(ODL, "OUT", None)
                call_old_state = getattr(ODL, "STATE_DIR", None)
                ODL.OUT = str(output_dir)
                ODL.STATE_DIR = str(output_dir / ".state")
                try:
                    ODL.dl_series(
                        str(item_id),
                        rng=range_spec or "all",
                        concurrency=max(1, concurrency),
                        retry_rounds=int(options.get("retry") or 2),
                        quality=quality,
                    )
                finally:
                    if call_old_out is None:
                        try:
                            delattr(ODL, "OUT")
                        except AttributeError:
                            pass
                    else:
                        ODL.OUT = call_old_out
                    if call_old_state is None:
                        try:
                            delattr(ODL, "STATE_DIR")
                        except AttributeError:
                            pass
                    else:
                        ODL.STATE_DIR = call_old_state

            # 收集 mp4（排除 .enc）
            paths = sorted(
                p
                for p in Path(output_dir).rglob("*.mp4")
                if p.is_file() and not p.name.endswith(".enc.mp4") and p.stat().st_size > 0
            )
            playable_paths = [p for p in paths if not p.name.endswith(".raw.mp4")]
            raw_paths = [p for p in paths if p.name.endswith(".raw.mp4")]
            paths = playable_paths or (raw_paths if allow_raw else [])
            if naming and paths:
                renamed: list[Path] = []
                for path in paths:
                    match = re.search(r"第\s*0*(\d+)\s*集", path.stem)
                    index = int(match.group(1)) if match else 0
                    if index <= 0:
                        renamed.append(path)
                        continue
                    target = path.with_name(
                        format_segment_filename(
                            index,
                            episode_titles.get(index) or f"第{index}集",
                            naming,
                            ext=".raw.mp4" if path.name.endswith(".raw.mp4") else ".mp4",
                        )
                    )
                    if target != path:
                        target.unlink(missing_ok=True)
                        path.replace(target)
                    renamed.append(target)
                paths = renamed
            if progress:
                progress(100.0, f"done {len(paths)} files")
            if not paths:
                if raw_paths:
                    raise RuntimeError(
                        f"hongguo quality {quality} uses proprietary ByteVC and produced only "
                        "a diagnostic raw-decrypted file; choose 1080p for a playable MP4"
                    )
                raise RuntimeError(
                    "hongguo download produced no mp4; check config.json + sign backend "
                    f"(vendor={vendor_ready()})"
                )
            return paths

        try:
            return await asyncio.to_thread(call_with_session_recovery, _run)
        except HongguoVendorError:
            raise
        except Exception as exc:  # noqa: BLE001
            from app.errors import format_platform_error

            raise RuntimeError(format_platform_error(exc)) from exc
