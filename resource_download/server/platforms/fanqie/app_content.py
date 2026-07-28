"""App 路径：reader/full 密文 + CryptManager 预言机 → HTML/纯文本。

密钥来源（按优先级）:
  1. 显式传入 key_b64 / key_version
  2. 环境变量 FANQIE_CONTENT_KEY / FANQIE_CONTENT_KEY_VERSION
  3. data/config/fanqie_content_key.json（会话密钥，可从设备 mmkv 导出）
  4. 默认会话密钥（极易过期，仅兜底）
"""

from __future__ import annotations

import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from platforms.fanqie.crypt_oracle import (
    DEFAULT_KEY_VERSION,
    DEFAULT_SESSION_KEY,
    FanqieCryptOracle,
    FanqieCryptError,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONTENT_KEY_FILE = _REPO_ROOT / "data" / "config" / "fanqie_content_key.json"


def _load_content_key_file() -> dict[str, Any]:
    try:
        if _CONTENT_KEY_FILE.is_file():
            return json.loads(_CONTENT_KEY_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self._skip = False
        if tag in {"p", "br", "h1", "h2", "h3", "div"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip and data:
            self._parts.append(data)

    def text(self) -> str:
        raw = "".join(self._parts)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def html_to_text(html: str) -> str:
    p = _TextExtractor()
    try:
        p.feed(html)
        return p.text()
    except Exception:
        # 粗暴去标签
        t = re.sub(r"<[^>]+>", "\n", html)
        return re.sub(r"\n{3,}", "\n\n", t).strip()


def resolve_key(key_b64: str | None = None) -> str:
    if key_b64:
        return key_b64
    env = os.environ.get("FANQIE_CONTENT_KEY")
    if env:
        return env
    file_key = _load_content_key_file().get("key_b64")
    if file_key:
        return str(file_key)
    return DEFAULT_SESSION_KEY


def resolve_version(version: int | None = None) -> int:
    if version is not None:
        return int(version)
    env = os.environ.get("FANQIE_CONTENT_KEY_VERSION")
    if env:
        return int(env)
    file_ver = _load_content_key_file().get("key_version")
    if file_ver is not None:
        try:
            return int(file_ver)
        except Exception:
            pass
    return DEFAULT_KEY_VERSION


def decrypt_chapter_content(
    cipher_b64: str,
    *,
    key_b64: str | None = None,
    key_version: int | None = None,
    oracle: FanqieCryptOracle | None = None,
    as_text: bool = True,
) -> dict[str, Any]:
    """解密一章 content 字段。返回 html/text。"""
    own = oracle is None
    o = oracle or FanqieCryptOracle()
    try:
        if not o.attached:
            o.attach()
        key = resolve_key(key_b64)
        ver = resolve_version(key_version)
        r = o.decrypt_raw(cipher_b64, key, ver)
        if not r.ok or not r.text:
            raise FanqieCryptError(r.error or "decrypt failed")
        html = r.text
        out: dict[str, Any] = {
            "ok": True,
            "html": html,
            "key_version": ver,
            "out_len": len(r.out_bytes or b""),
        }
        if as_text:
            out["text"] = html_to_text(html)
        return out
    finally:
        if own:
            o.close()
