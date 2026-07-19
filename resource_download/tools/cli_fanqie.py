#!/usr/bin/env python3
"""本地 CLI：直接调用 web_ssr（不经 HTTP 中转），兼容旧 download.py 用法。"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SERVER = REPO / "server"
sys.path.insert(0, str(SERVER))

from platforms.fanqie import web_ssr  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="番茄小说本地下载（CLI）")
    parser.add_argument("url", help="书籍页或章节页 URL")
    parser.add_argument("-o", "--output", default=".", help="输出目录")
    parser.add_argument("-d", "--delay", type=float, default=1.0)
    parser.add_argument("-c", "--cookie", default="")
    args = parser.parse_args()

    if args.cookie:
        web_ssr.set_cookie(args.cookie)

    url_type, url_id = web_ssr.parse_url(args.url)
    font_mapping: dict = {}
    if url_type == "reader":
        book_id, font_mapping = web_ssr.get_book_info_from_reader(url_id)
    else:
        book_id = url_id

    book_name, chapters, page_font = web_ssr.get_chapter_list(book_id)
    if page_font:
        font_mapping.update(page_font)

    output_dir = os.path.join(args.output, web_ssr.sanitize_filename(book_name))
    os.makedirs(output_dir, exist_ok=True)
    print(f"小说: {book_name}  共 {len(chapters)} 章  -> {output_dir}")

    downloaded = skipped = 0
    for i, ch in enumerate(chapters, 1):
        prefix = f"[{i}/{len(chapters)}]"
        if ch["is_locked"]:
            print(f"{prefix} 跳过锁定: {ch['title']}")
            skipped += 1
            continue
        print(f"{prefix} 下载: {ch['title']}...", end=" ", flush=True)
        try:
            title, content = web_ssr.download_chapter(ch["item_id"], font_mapping)
            path = os.path.join(output_dir, f"{i:03d}-{web_ssr.sanitize_filename(title)}.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n{content}\n")
            print("完成")
            downloaded += 1
        except Exception as e:  # noqa: BLE001
            print(f"失败: {e}")
        if i < len(chapters):
            time.sleep(args.delay)

    print(f"完成 {downloaded} 章，跳过 {skipped}")


if __name__ == "__main__":
    main()
