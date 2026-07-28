"""番茄小说平台适配器。"""

from __future__ import annotations

import asyncio
import re
import time
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.models import DetailResponse, PlatformName, SearchItem, SegmentInfo
from platforms.base import BasePlatform, ProgressCallback
from platforms.fanqie import web_ssr


def _parse_range(range_spec: str, total: int) -> set[int] | None:
    """返回 1-based 章节序号集合；None 表示全部。"""
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
            slice_rows = raw[start:end] if start < len(raw) else raw[:20]
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
            book_name, chapters, _font = web_ssr.get_chapter_list(book_id, cookie=cookie)
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
                segments=segments,
                extra={"chapter_count": len(segments)},
            )

        try:
            return await asyncio.to_thread(_load)
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
        cookie = options.get("cookie") or get_settings().fanqie_cookie or None
        delay = float(options.get("delay", get_settings().fanqie_delay))
        mode = options.get("mode", "web")
        naming = options.get("naming") if isinstance(options.get("naming"), dict) else {}
        download_cover = bool(options.get("download_cover"))
        download_desc = bool(options.get("download_desc"))

        def _run() -> list[Path]:
            from platforms.naming import format_segment_filename

            # App 模式：签名+解密均在 com.dragon.read 内完成，不依赖红果 App。
            # Web 模式：公开页 + 字体映射，亦不依赖红果。
            book_id = _normalize_book_id(item_id)
            book_name, chapters, font_mapping = web_ssr.get_chapter_list(book_id, cookie=cookie)
            selected = _parse_range(range_spec, len(chapters))

            work_dir = output_dir / web_ssr.sanitize_filename(book_name)
            work_dir.mkdir(parents=True, exist_ok=True)

            # 封面 / 简介（可选）
            if download_desc:
                try:
                    desc_path = work_dir / "简介.txt"
                    desc_path.write_text(
                        f"书名：{book_name}\nID：{book_id}\n章节数：{len(chapters)}\n",
                        encoding="utf-8",
                    )
                except Exception:
                    pass
            if download_cover:
                # Web 列表接口未必带封面 URL；占位说明文件，避免空开关无反馈
                try:
                    (work_dir / "封面.url.txt").write_text(
                        "封面图需详情接口提供 cover URL 后自动下载；当前写入占位。\n",
                        encoding="utf-8",
                    )
                except Exception:
                    pass

            parts: list[str] = [f"# {book_name}\n"]
            chapter_files: list[Path] = []
            total = len(chapters)
            done = 0
            skipped = 0

            oracle = None
            if mode == "app":
                from platforms.fanqie.app_content import resolve_key, resolve_version
                from platforms.fanqie.crypt_oracle import FanqieCryptOracle

                key = resolve_key()
                ver = resolve_version()
                oracle = FanqieCryptOracle()
                oracle.attach()

            try:
                for i, ch in enumerate(chapters, start=1):
                    if selected is not None and i not in selected:
                        continue

                    if mode == "web" and ch.get("is_locked"):
                        skipped += 1
                        parts.append(f"\n\n## {ch.get('title') or i}\n\n（已锁定，已跳过）\n")
                        continue

                    if progress:
                        progress(done / max(total, 1) * 100.0, f"下载第 {i}/{total} 章")

                    title = str(ch.get("title") or f"第 {i} 章")
                    plain = ""

                    if mode == "app":
                        from platforms.fanqie import client as app_client
                        from platforms.fanqie.app_content import html_to_text

                        try:
                            j = app_client.fetch_full(book_id, str(ch["item_id"]))
                            data = j.get("data") or {}
                            content = data.get("content") or ""
                            if not content:
                                raise RuntimeError(f"empty content: {j.get('message')}")

                            assert oracle is not None
                            r = oracle.decrypt_raw(content, key, ver)
                            if (not r.ok or not r.text) and data.get("key_version"):
                                try:
                                    alt = int(data["key_version"])
                                    if alt != ver:
                                        r = oracle.decrypt_raw(content, key, alt)
                                except Exception:
                                    pass

                            if not r.ok or not r.text:
                                raise RuntimeError(f"decrypt failed: {r.error}")

                            plain = html_to_text(r.text)
                            parts.append(f"\n\n## {title}\n\n{plain}\n")
                            done += 1
                        except Exception as e:
                            skipped += 1
                            plain = f"（App解密下载失败: {e}）"
                            parts.append(f"\n\n## {title}\n\n{plain}\n")
                    else:
                        title, content = web_ssr.download_chapter(
                            str(ch["item_id"]), font_mapping, cookie=cookie
                        )
                        plain = content
                        parts.append(f"\n\n## {title}\n\n{content}\n")
                        done += 1

                    # 按命名模板写单章 txt
                    if plain:
                        fname = format_segment_filename(i, title, naming, ext=".txt")
                        ch_path = work_dir / fname
                        ch_path.write_text(f"{title}\n\n{plain}\n", encoding="utf-8")
                        chapter_files.append(ch_path)

                    if i < total and delay > 0:
                        time.sleep(delay)
            finally:
                if oracle:
                    try:
                        oracle.close()
                    except Exception:
                        pass
                if mode == "app":
                    from platforms.fanqie import client as app_client

                    try:
                        app_client.get_oracle().close()
                    except Exception:
                        pass

            out_path = work_dir / f"{web_ssr.sanitize_filename(book_name)}.md"
            out_path.write_text("".join(parts), encoding="utf-8")
            if progress:
                progress(100.0, f"完成 {done} 章" + (f"，跳过 {skipped}" if skipped else ""))
            # 优先返回分章文件，便于「打开目录/文件」
            return chapter_files or [out_path]

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:  # noqa: BLE001
            from app.errors import format_platform_error

            raise RuntimeError(format_platform_error(exc)) from exc
