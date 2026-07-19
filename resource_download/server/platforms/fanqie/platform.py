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
        # MVP-1：搜索后置；若 query 是 URL/纯数字 ID，包装成单条结果
        q = query.strip()
        try:
            book_id = await asyncio.to_thread(_normalize_book_id, q)
        except Exception:
            return []
        detail = await self.get_detail(book_id, **kwargs)
        return [
            SearchItem(
                id=detail.id,
                title=detail.title,
                cover=detail.cover,
                author=detail.author,
                desc=detail.desc,
                extra={"note": "MVP-1 search resolves URL/ID only"},
            )
        ]

    async def get_detail(self, item_id: str, **kwargs: Any) -> DetailResponse:
        cookie = kwargs.get("cookie") or get_settings().fanqie_cookie or None

        def _load() -> DetailResponse:
            web_ssr.set_cookie(cookie)
            book_id = _normalize_book_id(item_id)
            book_name, chapters, _font = web_ssr.get_chapter_list(book_id)
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

        return await asyncio.to_thread(_load)

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

        def _run() -> list[Path]:
            web_ssr.set_cookie(cookie)
            book_id = _normalize_book_id(item_id)
            book_name, chapters, font_mapping = web_ssr.get_chapter_list(book_id)
            selected = _parse_range(range_spec, len(chapters))

            work_dir = output_dir / web_ssr.sanitize_filename(book_name)
            work_dir.mkdir(parents=True, exist_ok=True)

            parts: list[str] = [f"# {book_name}\n"]
            total = len(chapters)
            done = 0
            skipped = 0

            oracle = None
            if mode == "app":
                from platforms.fanqie import client as app_client
                from platforms.fanqie.app_content import html_to_text, resolve_key, resolve_version
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
                            parts.append(f"\n\n## {title}\n\n（App解密下载失败: {e}）\n")
                    else:
                        title, content = web_ssr.download_chapter(str(ch["item_id"]), font_mapping)
                        parts.append(f"\n\n## {title}\n\n{content}\n")
                        done += 1

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

            out_path = work_dir / f"{web_ssr.sanitize_filename(book_name)}.txt"
            out_path.write_text("".join(parts), encoding="utf-8")
            if progress:
                progress(100.0, f"完成 {done} 章，跳过/失败 {skipped}")
            return [out_path]

        return await asyncio.to_thread(_run)
