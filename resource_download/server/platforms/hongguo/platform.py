"""红果平台适配器：复用 vendor/hongguo 的 API + 下载解密。"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from app.models import DetailResponse, DiscoverItem, PlatformName, SearchItem, SegmentInfo
from platforms.base import BasePlatform, ProgressCallback
from platforms.hongguo.bridge import (
    HongguoVendorError,
    call_with_session_recovery,
    load_hongguo_api,
    load_offline_dl,
    vendor_ready,
)


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
            if kind == "hot":
                rows = H.browse(
                    "short_play",
                    sort="hot_score",
                    max_items=bounded_limit,
                ) or []
            elif kind == "new":
                rows = H.latest(
                    "short_play",
                    only_today=True,
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

    async def download(
        self,
        item_id: str,
        output_dir: Path,
        *,
        range_spec: str = "all",
        options: dict[str, Any] | None = None,
        progress: ProgressCallback | None = None,
    ) -> list[Path]:
        options = options or {}
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

            # 让上游下载落到我们的 job 目录
            ODL.OUT = str(output_dir)
            ODL.STATE_DIR = str(output_dir / ".state")

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
            ODL.dl_series(
                str(item_id),
                rng=range_spec or "all",
                concurrency=max(1, concurrency),
                retry_rounds=int(options.get("retry") or 2),
                quality=quality,
            )

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
