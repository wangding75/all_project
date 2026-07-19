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


def main() -> None:
    parser = argparse.ArgumentParser(description="Fanqie E2E via relay API")
    parser.add_argument(
        "--id",
        required=True,
        help="book_id 或 fanqienovel.com page/reader URL",
    )
    parser.add_argument("--range", default="1-2", dest="range_spec", help="all | 1-3 | 1,2")
    parser.add_argument("--out", default="data/e2e_downloads", help="保存下载文件的目录")
    parser.add_argument("--poll", type=float, default=2.0, help="轮询间隔秒")
    parser.add_argument("--timeout", type=float, default=600.0, help="任务超时秒")
    parser.add_argument("--skip-download", action="store_true", help="只跑到 job success")
    args = parser.parse_args()

    print(f"API_BASE={api_base()}")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    with client() as c:
        print("== detail ==")
        r = c.get("/v1/detail", params={"platform": "fanqie", "id": args.id})
        if r.status_code != 200:
            die(f"detail failed: {r.status_code} {r.text}")
        detail = r.json()
        print(f"title={detail.get('title')} id={detail.get('id')} segments={len(detail.get('segments') or [])}")

        print("== create job ==")
        r = c.post(
            "/v1/jobs",
            json={
                "platform": "fanqie",
                "id": args.id,
                "range": args.range_spec,
                "options": {},
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
            status = job.get("status")
            print(f"  status={status} progress={job.get('progress')} msg={job.get('message')}")
            if status in {"success", "failed", "cancelled"}:
                break
            time.sleep(args.poll)
        else:
            die("job timeout")

        if job.get("status") != "success":
            die(f"job not success:\n{pretty(job)}")

        files = job.get("files") or []
        if not files:
            die("job success but no files")

        if args.skip_download:
            print(pretty(job))
            print("OK (skip download)")
            return

        print("== download files ==")
        for f in files:
            file_id = f["file_id"]
            name = f.get("name") or Path(file_id).name
            r = c.get(f"/v1/files/{file_id}")
            if r.status_code != 200:
                die(f"download failed: {file_id} {r.status_code} {r.text}")
            dest = out_dir / name
            dest.write_bytes(r.content)
            print(f"  saved {dest} ({len(r.content)} bytes)")

    print("OK")


if __name__ == "__main__":
    main()
