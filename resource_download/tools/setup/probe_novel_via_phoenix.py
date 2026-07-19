"""用已跑通的红果(com.phoenix.read)签名，探测番茄小说正文相关 bookapi。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

# 复用 hongguo 模块
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "vendor" / "hongguo"))
sys.path.insert(0, str(ROOT / "vendor" / "hongguo" / "frida"))

os.environ.setdefault("ADB", r"D:\install\Netease\MuMu\nx_main\adb.exe")
os.environ.setdefault("ADB_DEVICE", "127.0.0.1:16384")
os.environ.setdefault("FRIDA_HOST", "127.0.0.1:27042")

import hongguo as H  # noqa: E402


def ensure_phoenix() -> None:
    adb, dev = H.ADB, H.DEV
    subprocess.run([adb, "connect", dev], capture_output=True)
    subprocess.run([adb, "-s", dev, "root"], capture_output=True)
    time.sleep(0.3)
    subprocess.run([adb, "connect", dev], capture_output=True)
    # prefer phoenix for signing
    subprocess.run([adb, "-s", dev, "shell", "am", "force-stop", "com.dragon.read"], capture_output=True)
    pid = subprocess.run(
        [adb, "-s", dev, "shell", "pidof", "com.phoenix.read"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not pid:
        subprocess.run(
            [adb, "-s", dev, "shell", "pkill", "-9", "frida-server"],
            capture_output=True,
        )
        time.sleep(0.5)
        subprocess.run(
            [
                adb,
                "-s",
                dev,
                "shell",
                "monkey",
                "-p",
                "com.phoenix.read",
                "-c",
                "android.intent.category.LAUNCHER",
                "1",
            ],
            capture_output=True,
        )
        time.sleep(10)
    ps = subprocess.run(
        [adb, "-s", dev, "shell", "ps", "-A"],
        capture_output=True,
        text=True,
    ).stdout
    if "frida-server" not in ps:
        subprocess.run(
            [adb, "-s", dev, "shell", "/data/local/tmp/frida-server -D &"],
            capture_output=True,
        )
        time.sleep(2)
    subprocess.run([adb, "-s", dev, "forward", "tcp:27042", "tcp:27042"], capture_output=True)
    # reset oracle singleton if any
    H._oracle = None
    print("phoenix pid", subprocess.run(
        [adb, "-s", dev, "shell", "pidof", "com.phoenix.read"],
        capture_output=True,
        text=True,
    ).stdout.strip())


def dump(j, n=400):
    s = json.dumps(j, ensure_ascii=False)
    print(s[:n] + ("..." if len(s) > n else ""))


def main() -> int:
    ensure_phoenix()
    book_id = "7590221243043826712"  # 这个游戏不对劲... 之前 Web 验证过

    print("\n=== 1 search novel keywords ===")
    for q in ("这个游戏不对劲", "北派寻宝笔记", "完美世界"):
        try:
            r = H.search(q)
            print(q, "hits", len(r or []))
            if r:
                print(" first", r[0].get("title"), r[0].get("series_id") or r[0].get("book_id"), "eps", r[0].get("episode_cnt"))
        except Exception as e:
            print(q, "ERR", e)

    print("\n=== 2 book detail/directory ===")
    for path, extra in [
        ("/reading/bookapi/detail/v", {"book_id": book_id}),
        ("/reading/bookapi/directory/all_items/v", {"book_id": book_id}),
        ("/reading/bookapi/directory/all_infos/v", {"book_id": book_id}),
        ("/reading/bookapi/directory/all_items/v/", {"book_id": book_id}),
    ]:
        try:
            j = H.api("GET", path, extra_query=extra)
            print(path, "code", j.get("code"), "keys", list(j.keys())[:12])
            dump(j, 350)
        except Exception as e:
            print(path, "ERR", e)

    print("\n=== 3 try find item_id then reader full ===")
    try:
        j = H.api("GET", "/reading/bookapi/directory/all_items/v", extra_query={"book_id": book_id})
        # walk for item_id
        text = json.dumps(j, ensure_ascii=False)
        import re

        ids = re.findall(r'"item_id"\s*:\s*"?(\d+)"?', text)
        ids = list(dict.fromkeys(ids))
        print("item_ids found", len(ids), ids[:5])
        if ids:
            item_id = ids[0]
            for path in (
                "/reading/reader/full/v",
                "/reading/reader/full/v/",
                "/reading/reader/batch_full/v",
            ):
                for method in ("GET", "POST"):
                    try:
                        if method == "GET":
                            jj = H.api(method, path, extra_query={"item_id": item_id, "book_id": book_id})
                        else:
                            jj = H.api(
                                method,
                                path,
                                extra_query={},
                                body={"item_ids": [item_id], "book_id": book_id},
                            )
                        print(method, path, "code", jj.get("code"), "keys", list(jj.keys())[:15])
                        dump(jj, 500)
                    except Exception as e:
                        print(method, path, "ERR", e)
    except Exception as e:
        print("directory ERR", e)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
