"""分集/章节文件命名（由客户端 settings 经 job.options.naming 传入）。"""

from __future__ import annotations

import re
from typing import Any


def _sanitize(name: str) -> str:
    text = (name or "").strip()
    text = re.sub(r'[\\/:*?"<>|]+', "_", text)
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text or "untitled"


def format_segment_filename(
    index: int,
    title: str | None,
    naming: dict[str, Any] | None = None,
    *,
    ext: str = ".txt",
) -> str:
    """生成如 ``01.空屋.txt`` / ``1-标题.txt``。"""
    naming = naming or {}
    use_prefix = naming.get("use_prefix", True)
    include_title = naming.get("include_title", True)
    number_style = str(naming.get("number_style") or "01")
    sep = str(naming.get("separator") if naming.get("separator") is not None else ".")

    n = max(1, int(index))
    if number_style == "001":
        num = f"{n:03d}"
    elif number_style == "1":
        num = str(n)
    else:
        num = f"{n:02d}"

    clean_title = _sanitize(str(title or "")) if include_title else ""
    parts: list[str] = []
    if use_prefix:
        parts.append(num)
    if include_title and clean_title:
        parts.append(clean_title)
    if not parts:
        parts.append(num)

    base = sep.join(parts) if sep else "".join(parts)
    if not ext.startswith("."):
        ext = f".{ext}"
    return f"{_sanitize(base)}{ext}"
