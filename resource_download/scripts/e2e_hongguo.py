#!/usr/bin/env python3
"""红果 E2E：search/detail → job → poll → 下载 mp4。

依赖:
  - server 已启动
  - vendor/hongguo + config.json + 签名后端可用

示例:
  python scripts/e2e_hongguo.py --id SERIES_ID --range 1-1
  python scripts/e2e_hongguo.py --search "皇后" --range 1-1
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import api_base, client, die, pretty  # noqa: E402


import os

def main() -> None:
    parser = argparse.ArgumentParser(description="Hongguo E2E via relay API")
    parser.add_argument("--id", default=os.environ.get("E2E_HONGGUO_ID", "").strip(), help="series_id (也可通过 E2E_HONGGUO_ID 环境变量提供)")
    parser.add_argument("--search", default="", help="若未给 id，先 search 取第一条")
    parser.add_argument("--range", default="1-1", dest="range_spec")
    parser.add_argument("--quality", default="best")
    parser.add_argument("--out", default="data/e2e_downloads")
    parser.add_argument("--poll", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=3600.0)
    args = parser.parse_args()

    series_id = args.id.strip()

    if not series_id and not args.search.strip():
        print("[SKIP] Neither --id/--search nor E2E_HONGGUO_ID env var provided. Skipping Hongguo E2E test.")
        sys.exit(0)

    print(f"API_BASE={api_base()}")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    with client() as c:
        if not series_id:
            if not args.search:
                die("need --id or --search")
            print("== search ==")
            r = c.get("/v1/search", params={"platform": "hongguo", "q": args.search})
            if r.status_code != 200:
                die(f"search failed: {r.status_code} {r.text}")
            payload = r.json()
            # 兼容 SearchResponse {items:[...]} 与旧 list
            items = payload if isinstance(payload, list) else (payload.get("items") or [])
            if not items:
                die("search empty")
            series_id = str(items[0]["id"])
            print(f"pick id={series_id} title={items[0].get('title')} platform={items[0].get('platform')}")

        print("== detail ==")
        r = c.get("/v1/detail", params={"platform": "hongguo", "id": series_id})
        if r.status_code != 200:
            die(f"detail failed: {r.status_code} {r.text}")
        detail = r.json()
        print(
            f"title={detail.get('title')} segments={len(detail.get('segments') or [])}"
        )

        print("== create job ==")
        die(
            "BLOCKED: this legacy E2E client only has X-API-Key and cannot create a "
            "License-Protected job; use scripts/license_e2e.py with Device Proof V3.",
            code=2,
        )

    print("OK")


if __name__ == "__main__":
    main()
