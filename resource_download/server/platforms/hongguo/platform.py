"""红果平台适配器：复用 vendor/hongguo 的 API + 下载解密。"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from app.models import DetailResponse, PlatformName, SearchItem, SegmentInfo
from platforms.base import BasePlatform, ProgressCallback
from platforms.hongguo.bridge import (
    HongguoVendorError,
    load_hongguo_api,
    load_offline_dl,
    vendor_ready,
)


class HongguoPlatform(BasePlatform):
    name = PlatformName.hongguo.value

    async def search(self, query: str, page: int = 1, **kwargs: Any) -> list[SearchItem]:
        def _run() -> list[SearchItem]:
            H = load_hongguo_api()
            # 上游 search(query, max_items=None) — page 暂不映射
            raw = H.search(query) or []
            items: list[SearchItem] = []
            for row in raw:
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
                        extra=extra,
                    )
                )
            return items

        try:
            return await asyncio.to_thread(_run)
        except HongguoVendorError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"hongguo search failed: {exc}") from exc

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
            return await asyncio.to_thread(_run)
        except HongguoVendorError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"hongguo detail failed: {exc}") from exc

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

        def _run() -> list[Path]:
            H = load_hongguo_api()
            ODL = load_offline_dl()
            output_dir.mkdir(parents=True, exist_ok=True)

            # 让上游下载落到我们的 job 目录
            ODL.OUT = str(output_dir)
            ODL.STATE_DIR = str(output_dir / ".state")

            if progress:
                progress(1.0, "prepare series")

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
            if progress:
                progress(100.0, f"done {len(paths)} files")
            if not paths:
                raise RuntimeError(
                    "hongguo download produced no mp4; check config.json + sign backend "
                    f"(vendor={vendor_ready()})"
                )
            return paths

        try:
            return await asyncio.to_thread(_run)
        except HongguoVendorError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"hongguo download failed: {exc}") from exc
