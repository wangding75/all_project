"""脚本公共：读取 API_BASE / API_KEY。"""

from __future__ import annotations

import os
import sys
from typing import Any

import httpx

DEFAULT_BASE = "http://127.0.0.1:8000"
DEFAULT_KEY = "dev-key-change-me"


def api_base() -> str:
    return os.environ.get("API_BASE", DEFAULT_BASE).rstrip("/")


def api_key() -> str:
    return os.environ.get("API_KEY", DEFAULT_KEY)


def client() -> httpx.Client:
    # trust_env=False：避免系统 HTTP(S)_PROXY/SOCKS 干扰本机 127.0.0.1
    return httpx.Client(
        base_url=api_base(),
        headers={"X-API-Key": api_key()},
        timeout=60.0,
        trust_env=False,
    )


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def pretty(data: Any) -> str:
    import json

    return json.dumps(data, ensure_ascii=False, indent=2)
