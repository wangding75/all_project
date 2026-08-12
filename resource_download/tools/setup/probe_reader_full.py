"""拉取一章 reader/full，打印结构并尝试常见解压/解密。"""
from __future__ import annotations

import base64
import gzip
import json
import os
import subprocess
import sys
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "vendor" / "hongguo"))
sys.path.insert(0, str(ROOT / "vendor" / "hongguo" / "frida"))
os.environ.setdefault("ADB", r"D:\install\Netease\MuMu\nx_main\adb.exe")
from rd_device import resolve_device

os.environ["ADB_DEVICE"] = resolve_device()
os.environ.setdefault("FRIDA_HOST", "127.0.0.1:27042")

import hongguo as H  # noqa: E402

BOOK = "7590221243043826712"
ITEM = "7590221427400262168"  # 第1章


def ensure():
    adb, dev = H.ADB, H.DEV
    subprocess.run([adb, "connect", dev], capture_output=True)
    subprocess.run([adb, "-s", dev, "root"], capture_output=True)
    time.sleep(0.3)
    subprocess.run([adb, "connect", dev], capture_output=True)
    pid = subprocess.run(
        [adb, "-s", dev, "shell", "pidof", "com.phoenix.read"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not pid:
        subprocess.run([adb, "-s", dev, "shell", "pkill", "-9", "frida-server"], capture_output=True)
        time.sleep(0.5)
        subprocess.run(
            [adb, "-s", dev, "shell", "monkey", "-p", "com.phoenix.read",
             "-c", "android.intent.category.LAUNCHER", "1"],
            capture_output=True,
        )
        time.sleep(10)
    ps = subprocess.run([adb, "-s", dev, "shell", "ps", "-A"], capture_output=True, text=True).stdout
    if "frida-server" not in ps:
        subprocess.run([adb, "-s", dev, "shell", "/data/local/tmp/frida-server -D &"], capture_output=True)
        time.sleep(2)
    subprocess.run([adb, "-s", dev, "forward", "tcp:27042", "tcp:27042"], capture_output=True)
    H._oracle = None


def try_decode(label: str, raw: bytes):
    print(f"\n-- try {label} len={len(raw)} head={raw[:16].hex()}")
    for name, fn in [
        ("utf8", lambda b: b.decode("utf-8")),
        ("gzip", lambda b: gzip.decompress(b).decode("utf-8", "replace")),
        ("zlib", lambda b: zlib.decompress(b).decode("utf-8", "replace")),
        ("zlib-raw", lambda b: zlib.decompress(b, -zlib.MAX_WBITS).decode("utf-8", "replace")),
    ]:
        try:
            t = fn(raw)
            print(f"  OK {name}: {t[:200]!r}")
            return t
        except Exception as e:
            print(f"  fail {name}: {type(e).__name__}")
    return None


def main():
    ensure()
    j = H.api(
        "GET",
        "/reading/reader/full/v",
        extra_query={"item_id": ITEM, "book_id": BOOK, "novel_id": BOOK},
    )
    out = ROOT / "tmp" / "fanqie_probe"
    out.mkdir(parents=True, exist_ok=True)
    (out / "full_resp.json").write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")
    print("code", j.get("code"), "keys", list(j.keys()))
    data = j.get("data") or {}
    print("data keys", list(data.keys()) if isinstance(data, dict) else type(data))
    if not isinstance(data, dict):
        return 1
    for k, v in data.items():
        if k == "content":
            print("content type", type(v).__name__, "len", len(v) if hasattr(v, "__len__") else "")
            print("content head", str(v)[:120])
        elif isinstance(v, (str, int, float, bool)) or v is None:
            print(f"  {k}: {v}")
        elif isinstance(v, dict):
            print(f"  {k}: dict keys={list(v.keys())[:20]}")
        elif isinstance(v, list):
            print(f"  {k}: list len={len(v)}")
        else:
            print(f"  {k}: {type(v)}")

    content = data.get("content") or ""
    # base64?
    for pad in ("", "=", "==", "==="):
        try:
            raw = base64.b64decode(content + pad)
            print("\nb64 decode ok", len(raw))
            try_decode("b64", raw)
            (out / "content.bin").write_bytes(raw)
            break
        except Exception:
            continue
    else:
        # maybe already text
        try_decode("as-bytes", content.encode("utf-8", "replace"))

    # common key fields
    for k in ("key", "crypt_key", "crypt_status", "compress_status", "content_key",
              "secret_key", "aes_key", "title", "novel_name", "chapter_title"):
        if k in data:
            print("field", k, data[k] if not isinstance(data[k], str) or len(str(data[k])) < 80 else str(data[k])[:80])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
