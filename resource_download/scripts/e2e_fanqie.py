#!/usr/bin/env python3
"""番茄 E2E：detail → create job → poll → 下载 TXT。

示例:
  set API_BASE=http://127.0.0.1:8000
  set API_KEY=dev-key-change-me
  python scripts/e2e_fanqie.py --id https://fanqienovel.com/page/BOOK_ID --range 1-2
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
    parser = argparse.ArgumentParser(description="Fanqie E2E via relay API")
    parser.add_argument(
        "--id",
        default=os.environ.get("E2E_FANQIE_ID", "").strip(),
        help="book_id 或 fanqienovel.com page/reader URL (也可以通过 E2E_FANQIE_ID 环境变量提供)",
    )
    parser.add_argument("--range", default="1-2", dest="range_spec", help="all | 1-3 | 1,2")
    parser.add_argument("--out", default="data/e2e_downloads", help="保存下载文件的目录")
    parser.add_argument("--poll", type=float, default=2.0, help="轮询间隔秒")
    parser.add_argument("--timeout", type=float, default=600.0, help="任务超时秒")
    parser.add_argument("--skip-download", action="store_true", help="只跑到 job success")
    args = parser.parse_args()

    sample_id = args.id.strip()
    if not sample_id:
        print("[SKIP] Neither --id nor E2E_FANQIE_ID env var provided. Skipping Fanqie E2E test.")
        sys.exit(0)

    print(f"API_BASE={api_base()}")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    with client() as c:
        print("== detail ==")
        r = c.get("/v1/detail", params={"platform": "fanqie", "id": sample_id})
        if r.status_code != 200:
            die(f"detail failed: {r.status_code} {r.text}")
        detail = r.json()
        print(f"title={detail.get('title')} id={detail.get('id')} segments={len(detail.get('segments') or [])}")

        print("== create job ==")
        die(
            "BLOCKED: this legacy E2E client only has X-API-Key and cannot create a "
            "License-Protected job; use scripts/license_e2e.py with Device Proof V3.",
            code=2,
        )

    print("OK")


if __name__ == "__main__":
    main()
