"""番茄小说平台适配器。"""

from __future__ import annotations

import asyncio
import re
from typing import Any

from app.config import get_settings
from app.models import DetailResponse, DiscoverItem, PlatformName, SearchItem, SegmentInfo
from platforms.base import BasePlatform
from platforms.fanqie import web_ssr


def _parse_range(range_spec: str, total: int) -> set[int] | None:
    """Return a bounded set of 1-based chapter numbers; ``None`` means all."""
    from app.options import validate_range_spec

    range_spec = validate_range_spec(range_spec)
    raw = (range_spec or "all").strip().lower()
    if raw in {"", "all", "*"}:
        return None
    selected: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start, end = int(a), int(b)
            if start > end:
                start, end = end, start
            selected.update(range(start, end + 1))
        else:
            selected.add(int(part))
    return selected


def _normalize_book_id(item_id: str) -> str:
    text = item_id.strip()
    if "fanqienovel.com" in text:
        url_type, url_id = web_ssr.parse_url(text)
        if url_type == "reader":
            book_id, _ = web_ssr.get_book_info_from_reader(url_id)
            return book_id
        return url_id
    if re.fullmatch(r"\d+", text):
        return text
    raise ValueError(f"无法识别的番茄 ID/URL: {item_id}")


class FanqiePlatform(BasePlatform):
    name = PlatformName.fanqie.value

    async def discover(
        self,
        kind: str,
        *,
        limit: int = 24,
        **kwargs: Any,
    ) -> list[DiscoverItem]:
        """番茄官网真实热读推荐与最近更新。"""

        def _load() -> list[DiscoverItem]:
            rows = web_ssr.get_home_discover(kind, limit=limit)
            return [
                DiscoverItem(
                    rank=index if kind == "hot" else None,
                    id=str(row["book_id"]),
                    title=str(row["title"]),
                    cover=str(row["cover"]) if row.get("cover") else None,
                    author=str(row["author"]) if row.get("author") else None,
                    desc=str(row["desc"]) if row.get("desc") else None,
                    platform=PlatformName.fanqie,
                    source_label="番茄小说",
                    badge="热" if kind == "hot" else "新",
                    extra={
                        "category": row.get("category"),
                        "update_time": row.get("update_time"),
                        "latest_chapter": row.get("latest_chapter"),
                    },
                )
                for index, row in enumerate(rows, start=1)
            ]

        try:
            return await asyncio.to_thread(_load)
        except Exception as exc:  # noqa: BLE001
            from app.errors import format_platform_error

            raise RuntimeError(format_platform_error(exc)) from exc

    async def search(self, query: str, page: int = 1, **kwargs: Any) -> list[SearchItem]:
        """支持：书名关键词（App 签名搜索）/ 书 ID / fanqienovel URL。

        关键词搜索走 platforms.fanqie.client（需服务端 Frida + fanqie_config）。
        纯数字 ID 或页面 URL 走 Web 详情包装为单条结果（无需关键词搜索接口）。
        """
        q = query.strip()
        if not q:
            return []

        # 1) URL / 纯数字 ID → 详情包装
        try:
            book_id = await asyncio.to_thread(_normalize_book_id, q)
        except Exception:
            book_id = None

        if book_id is not None:
            detail = await self.get_detail(book_id, **kwargs)
            return [
                SearchItem(
                    id=detail.id,
                    title=detail.title,
                    cover=detail.cover,
                    author=detail.author,
                    desc=detail.desc,
                    platform=PlatformName.fanqie,
                    source_label="番茄小说",
                    extra={"note": "resolved from id/url"},
                )
            ]

        # 2) 书名关键词 → App API 搜索（Frida 签名，必须限时，避免 UI 一直「搜索中」）
        def _keyword_search() -> list[SearchItem]:
            from platforms.fanqie import client as app_client

            max_items = min(50, max(20, page * 20))
            raw = app_client.search(q, max_items=max_items) or []
            start = (page - 1) * 20
            end = start + 20
            slice_rows = raw[start:end] if start < len(raw) else []
            items: list[SearchItem] = []
            for row in slice_rows:
                bid = str(row.get("book_id") or "")
                if not bid:
                    continue
                items.append(
                    SearchItem(
                        id=bid,
                        title=str(row.get("title") or bid),
                        cover=str(row["cover"]) if row.get("cover") else None,
                        author=str(row["author"]) if row.get("author") else None,
                        desc=str(row["desc"]) if row.get("desc") else None,
                        platform=PlatformName.fanqie,
                        source_label="番茄小说",
                        extra={"source": "app_search"},
                    )
                )
            return items

        def _keyword_search_bounded() -> list[SearchItem]:
            import concurrent.futures

            # Frida attach 偶发卡死：线程超时后必须让请求结束
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(_keyword_search)
                try:
                    return fut.result(timeout=18.0)
                except concurrent.futures.TimeoutError as exc:
                    # 尝试关闭签名会话，避免占死
                    try:
                        from platforms.fanqie import client as app_client

                        app_client.get_oracle().close()
                    except Exception:
                        pass
                    raise TimeoutError(
                        "番茄书名搜索超时（签名/Frida）。请确认模拟器番茄与 sys_hlpd 正常，"
                        "或改用书籍数字 ID 搜索。"
                    ) from exc

        try:
            return await asyncio.to_thread(_keyword_search_bounded)
        except Exception as exc:  # noqa: BLE001
            from app.errors import format_platform_error

            raise RuntimeError(
                format_platform_error(exc)
                or f"番茄关键词搜索失败（需服务端 App 签名环境）: {exc}"
            ) from exc

    async def get_detail(self, item_id: str, **kwargs: Any) -> DetailResponse:
        cookie = kwargs.get("cookie") or get_settings().fanqie_cookie or None

        def _load() -> DetailResponse:
            book_id = _normalize_book_id(item_id)
            book_name, chapters, _font, meta = web_ssr.get_book_page(book_id, cookie=cookie)
            segments = [
                SegmentInfo(
                    id=str(ch["item_id"]),
                    title=str(ch.get("title") or f"第{i}章"),
                    index=i,
                    locked=bool(ch.get("is_locked")),
                )
                for i, ch in enumerate(chapters, start=1)
            ]
            return DetailResponse(
                platform=PlatformName.fanqie,
                id=book_id,
                title=book_name,
                cover=str(meta.get("cover") or "") or None,
                author=str(meta.get("author") or "") or None,
                desc=str(meta.get("abstract") or "") or None,
                segments=segments,
                extra={"chapter_count": len(segments), **meta},
            )

        try:
            return await asyncio.to_thread(_load)
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
        """Issue a short-lived proxy descriptor for server-side text resolve.

        Fanqie chapter decoding stays in this adapter.  The client receives a
        plain streamed text response and never receives App cookies, Session,
        signing or Frida state.
        """
        detail = await self.get_detail(resource_id, **(options or {}))
        return [
            {
                "platform": self.name,
                "resource_id": detail.id,
                "title": title or detail.title,
                "media_type": "text/markdown; charset=utf-8",
                "suggested_filename": f"{title or detail.title}.md",
                "download_mode": "proxy",
                "range_supported": False,
                "extra": {"chapter_count": len(detail.segments)},
            }
        ]

    async def stream_download(
        self,
        resource_id: str,
        *,
        range_spec: str = "all",
        options: dict[str, Any] | None = None,
    ):
        """Stream Fanqie chapters without creating a server-side output file."""
        options = dict(options or {})

        def _prepare():
            book_id = _normalize_book_id(resource_id)
            book_name, chapters, font_mapping, _meta = web_ssr.get_book_page(
                book_id,
                cookie=options.get("cookie") or get_settings().fanqie_cookie or None,
            )
            selected = _parse_range(range_spec, len(chapters))
            return book_name, chapters, font_mapping, selected

        book_name, chapters, font_mapping, selected = await asyncio.to_thread(_prepare)
        yield f"# {book_name}\n".encode("utf-8")
        cookie = options.get("cookie") or get_settings().fanqie_cookie or None
        for index, chapter in enumerate(chapters, start=1):
            if selected is not None and index not in selected:
                continue
            chapter_title, content = await asyncio.to_thread(
                web_ssr.download_chapter,
                str(chapter["item_id"]),
                font_mapping,
                cookie=cookie,
            )
            yield f"\n\n## {chapter_title}\n\n{content}\n".encode("utf-8")
