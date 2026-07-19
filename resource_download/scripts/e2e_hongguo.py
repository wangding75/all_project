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


def main() -> None:
    parser = argparse.ArgumentParser(description="Hongguo E2E via relay API")
    parser.add_argument("--id", default="", help="series_id")
    parser.add_argument("--search", default="", help="若未给 id，先 search 取第一条")
    parser.add_argument("--range", default="1-1", dest="range_spec")
    parser.add_argument("--quality", default="best")
    parser.add_argument("--out", default="data/e2e_downloads")
    parser.add_argument("--poll", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=3600.0)
    args = parser.parse_args()

    print(f"API_BASE={api_base()}")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    series_id = args.id.strip()

    with client() as c:
        if not series_id:
            if not args.search:
                die("need --id or --search")
            print("== search ==")
            r = c.get("/v1/search", params={"platform": "hongguo", "q": args.search})
            if r.status_code != 200:
                die(f"search failed: {r.status_code} {r.text}")
            items = r.json()
            if not items:
                die("search empty")
            series_id = str(items[0]["id"])
            print(f"pick id={series_id} title={items[0].get('title')}")

        print("== detail ==")
        r = c.get("/v1/detail", params={"platform": "hongguo", "id": series_id})
        if r.status_code != 200:
            die(f"detail failed: {r.status_code} {r.text}")
        detail = r.json()
        print(
            f"title={detail.get('title')} segments={len(detail.get('segments') or [])}"
        )

        print("== create job ==")
        r = c.post(
            "/v1/jobs",
            json={
                "platform": "hongguo",
                "id": series_id,
                "range": args.range_spec,
                "options": {"quality": args.quality, "concurrency": 1},
            },
        )
        if r.status_code != 200:
            die(f"create job failed: {r.status_code} {r.text}")
        job = r.json()
        job_id = job["job_id"]
        print(f"job_id={job_id}")

        print("== poll ==")
        deadline = time.time() + args.timeout
        while time.time() < deadline:
            r = c.get(f"/v1/jobs/{job_id}")
            if r.status_code != 200:
                die(f"get job failed: {r.status_code} {r.text}")
            job = r.json()
            print(
                f"  status={job.get('status')} progress={job.get('progress')} "
                f"msg={job.get('message')} err={job.get('error')}"
            )
            if job.get("status") in {"success", "failed", "cancelled"}:
                break
            time.sleep(args.poll)
        else:
            die("job timeout")

        if job.get("status") != "success":
            die(f"job not success:\n{pretty(job)}")

        print("== download files ==")
        for f in job.get("files") or []:
            file_id = f["file_id"]
            name = f.get("name") or Path(file_id).name
            r = c.get(f"/v1/files/{file_id}")
            if r.status_code != 200:
                die(f"file failed: {file_id} {r.status_code}")
            dest = out_dir / name
            dest.write_bytes(r.content)
            print(f"  saved {dest} ({len(r.content)} bytes)")

    print("OK")


if __name__ == "__main__":
    main()
